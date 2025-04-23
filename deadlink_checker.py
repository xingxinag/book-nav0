import os
import sys
from app import create_app, db
from app.models import Website, DeadlinkCheck
import requests
import uuid
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
import click
import queue
from datetime import datetime

app = create_app()

def check_single_link_thread_safe(website, check_id, result_queue):
    """线程安全的链接检测函数，不直接操作数据库"""
    url = website.url
    is_valid = False
    status_code = None
    error_type = None
    error_message = None
    start_time = time.time()
    
    # 确保URL有效
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        error_type = 'invalid_url'
        error_message = 'URL格式无效'
        response_time = 0
        
        # 将结果放入队列
        result = (website.id, url, is_valid, status_code, error_type, error_message, response_time)
        result_queue.put(result)
        return (False, url, error_type, error_message)
    
    try:
        # 发送HTTP请求检查链接
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        # 尝试HEAD请求，更轻量和快速
        try:
            response = requests.head(url, timeout=15, headers=headers, allow_redirects=True, verify=False)
            status_code = response.status_code
            
            # 有些网站可能不支持HEAD请求，如果得到4xx或5xx状态码，尝试GET请求
            if status_code >= 400:
                raise requests.exceptions.RequestException("HEAD请求失败，尝试GET请求")
                
        except requests.exceptions.RequestException:
            # 尝试GET请求，但只获取头部内容以节省带宽
            response = requests.get(url, timeout=15, headers=headers, allow_redirects=True, stream=True, verify=False)
            # 只读取少量内容
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # 过滤掉保持活动的新行
                    break
            status_code = response.status_code
            response.close()
        
        # 2xx和3xx状态码通常表示链接有效
        # 某些特殊的4xx状态码也可能表示网站正常工作，只是访问受限
        is_valid = (200 <= status_code < 400) or status_code in [401, 403]
        
        if not is_valid:
            error_type = f'http_{status_code}'
            error_message = f'HTTP状态码: {status_code}'
            
    except requests.exceptions.Timeout:
        error_type = 'timeout'
        error_message = '请求超时'
    except requests.exceptions.SSLError:
        error_type = 'ssl_error'
        error_message = 'SSL证书验证失败'
    except requests.exceptions.ConnectionError:
        error_type = 'connection_error'
        error_message = '连接错误'
    except requests.exceptions.TooManyRedirects:
        error_type = 'too_many_redirects'
        error_message = '重定向次数过多'
    except requests.exceptions.RequestException as e:
        error_type = 'request_error'
        error_message = str(e)
    except Exception as e:
        error_type = 'unknown_error'
        error_message = str(e)
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    # 将结果放入队列，而不是直接操作数据库
    result = (website.id, url, is_valid, status_code, error_type, error_message, response_time)
    result_queue.put(result)
    
    return (is_valid, url, error_type, error_message)

def process_check_results(result_queue, check_id, task_running, total_processed, total_valid, total_invalid):
    """处理检测结果队列中的数据"""
    with app.app_context():
        while True:
            try:
                # 从队列获取结果，最多等待5秒
                result = result_queue.get(timeout=5)
                
                # 如果收到None，表示任务结束
                if result is None:
                    break
                
                # 解析结果
                website_id, url, is_valid, status_code, error_type, error_message, response_time = result
                
                # 更新统计信息
                total_processed[0] += 1
                if is_valid:
                    total_valid[0] += 1
                else:
                    total_invalid[0] += 1
                
                # 保存到数据库
                try:
                    check_result = DeadlinkCheck(
                        check_id=check_id,
                        website_id=website_id,
                        url=url,
                        is_valid=is_valid,
                        status_code=status_code,
                        error_type=error_type,
                        error_message=error_message,
                        response_time=response_time,
                        checked_at=datetime.now()
                    )
                    db.session.add(check_result)
                    db.session.commit()
                except Exception as e:
                    print(f"保存检测结果失败: {str(e)}")
                    db.session.rollback()
                
                # 标记任务完成
                result_queue.task_done()
                
            except queue.Empty:
                # 队列为空，检查是否任务已结束
                if not task_running[0]:
                    break
            except Exception as e:
                print(f"处理检测结果时出错: {str(e)}")

@click.command()
@click.option('--max-workers', default=5, help='最大线程数')
@click.option('--batch-size', default=20, help='每批处理的链接数量')
def run_deadlink_check(max_workers, batch_size):
    """运行死链检测"""
    with app.app_context():
        # 确保DeadlinkCheck表存在
        inspector = db.inspect(db.engine)
        if not inspector.has_table('deadlink_check'):
            print("创建DeadlinkCheck表...")
            DeadlinkCheck.__table__.create(db.engine)
            print("DeadlinkCheck表创建成功！")
            
        # 获取所有网站
        websites = Website.query.all()
        total_websites = len(websites)
        print(f"共有 {total_websites} 个链接需要检测")
        
        # 生成检测批次ID
        check_id = str(uuid.uuid4())
        print(f"检测批次ID: {check_id}")
        
        # 创建队列和共享变量
        result_queue = queue.Queue()
        task_running = [True]  # 使用列表包装布尔值使其可变
        total_processed = [0]
        total_valid = [0]
        total_invalid = [0]
        
        # 启动结果处理线程
        processor = Thread(
            target=process_check_results, 
            args=(result_queue, check_id, task_running, total_processed, total_valid, total_invalid),
            daemon=True
        )
        processor.start()
        
        # 开始时间
        start_time = time.time()
        
        # 使用线程池进行并行检测
        max_workers = min(max_workers, total_websites)
        print(f"使用 {max_workers} 个线程进行检测")
        
        # 分批处理链接
        total_batches = (total_websites + batch_size - 1) // batch_size
        for i in range(0, total_websites, batch_size):
            batch = websites[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"\n------- 处理批次 {batch_num}/{total_batches}，包含 {len(batch)} 个链接 -------")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交当前批次的任务
                future_to_website = {
                    executor.submit(check_single_link_thread_safe, website, check_id, result_queue): website
                    for website in batch
                }
                
                # 处理结果展示（不处理数据库操作）
                for future in as_completed(future_to_website):
                    website = future_to_website[future]
                    try:
                        result = future.result()
                        
                        if result[0]:  # 链接有效
                            print(f"[{total_processed[0]+1}/{total_websites}] ✅ 有效: {website.url}")
                        else:  # 链接无效
                            print(f"[{total_processed[0]+1}/{total_websites}] ❌ 无效: {website.url} - {result[2]}: {result[3]}")
                            
                    except Exception as e:
                        print(f"[{total_processed[0]+1}/{total_websites}] ❌ 错误: {website.url} - {str(e)}")
            
            # 每完成一个批次，显示当前进度
            current_time = time.time()
            elapsed_so_far = current_time - start_time
            
            print(f"\n批次 {batch_num}/{total_batches} 完成")
            print(f"当前进度: {total_processed[0]}/{total_websites} ({total_processed[0]*100/total_websites:.1f}%)")
            print(f"有效链接: {total_valid[0]}，无效链接: {total_invalid[0]}")
            
            minutes, seconds = divmod(int(elapsed_so_far), 60)
            print(f"已用时间: {int(minutes)}分{int(seconds)}秒")
            
            if total_processed[0] > 0:
                estimated_total = elapsed_so_far * total_websites / total_processed[0]
                estimated_remaining = estimated_total - elapsed_so_far
                est_minutes, est_seconds = divmod(int(estimated_remaining), 60)
                print(f"预计剩余时间: {int(est_minutes)}分{int(est_seconds)}秒")
            
            # 让系统休息一下，避免资源占用过高
            time.sleep(1)
        
        # 计算总耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        # 告诉处理线程任务结束
        task_running[0] = False
        result_queue.put(None)  # 发送结束信号
        
        # 等待处理线程完成剩余工作
        processor.join(timeout=30)
        
        # 输出结果摘要
        print("\n========== 检测结果摘要 ==========")
        print(f"共检测 {total_processed[0]} 个链接")
        print(f"有效链接: {total_valid[0]} 个")
        print(f"无效链接: {total_invalid[0]} 个")
        print(f"检测用时: {int(minutes)}分{int(seconds)}秒")
        print(f"检测批次ID: {check_id}")
        print("==================================")
        
        if total_invalid[0] > 0:
            print("\n无效链接列表:")
            invalid_checks = DeadlinkCheck.query.filter_by(check_id=check_id, is_valid=False).all()
            for i, check in enumerate(invalid_checks, 1):
                website = Website.query.get(check.website_id)
                if website:
                    print(f"{i}. {website.title} ({website.url}) - {check.error_type}: {check.error_message}")

if __name__ == '__main__':
    run_deadlink_check() 