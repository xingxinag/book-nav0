from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required
from app import db, csrf
from app.main import bp
from app.models import Category, Website
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

@bp.route('/')
def index():
    categories = Category.query.order_by(Category.order.asc()).all()
    
    # 获取推荐网站，只显示公开的或当前用户可见的
    featured_sites_query = Website.query.filter_by(is_featured=True)
    if not current_user.is_authenticated:
        featured_sites_query = featured_sites_query.filter_by(is_private=False)
    elif not current_user.is_admin:
        featured_sites_query = featured_sites_query.filter(
            (Website.is_private == False) |  # 公开的
            (Website.created_by_id == current_user.id) |  # 自己创建的
            (Website.visible_to.contains(str(current_user.id)))  # 被授权查看的
        )
    featured_sites = featured_sites_query.order_by(Website.views.desc()).limit(6).all()
    
    # 预先加载每个分类下的网站，按照自定义排序顺序
    for category in categories:
        websites_query = Website.query.filter_by(category_id=category.id)
        if not current_user.is_authenticated:
            websites_query = websites_query.filter_by(is_private=False)
        elif not current_user.is_admin:
            websites_query = websites_query.filter(
                (Website.is_private == False) |
                (Website.created_by_id == current_user.id) |
                (Website.visible_to.contains(str(current_user.id)))
            )
        category.website_list = websites_query.order_by(
            Website.sort_order.desc(), 
            Website.views.desc()
        ).all()
        
    return render_template('index.html', 
                         title='首页', 
                         categories=categories, 
                         featured_sites=featured_sites)

@bp.route('/category/<int:id>')
def category(id):
    category = Category.query.get_or_404(id)
    
    # 构建查询
    websites_query = Website.query.filter_by(category_id=id)
    
    # 根据用户权限过滤私有链接
    if not current_user.is_authenticated:
        websites_query = websites_query.filter_by(is_private=False)
    elif not current_user.is_admin:
        websites_query = websites_query.filter(
            (Website.is_private == False) |
            (Website.created_by_id == current_user.id) |
            (Website.visible_to.contains(str(current_user.id)))
        )
    
    websites = websites_query.order_by(
        Website.sort_order.desc(), 
        Website.views.desc()
    ).all()
    
    return render_template('category.html', 
                         title=category.name, 
                         category=category, 
                         websites=websites)

@bp.route('/site/<int:id>')
def site(id):
    site = Website.query.get_or_404(id)
    
    # 更新访问量
    site.views += 1
    
    # 更新最后访问时间
    site.last_view = datetime.utcnow()
    
    db.session.commit()
    return redirect(site.url)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    
    # 构建搜索查询
    websites_query = Website.query.filter(
        Website.title.contains(query) |
        Website.description.contains(query) |
        Website.url.contains(query)
    )
    
    # 根据用户权限过滤私有链接
    if not current_user.is_authenticated:
        websites_query = websites_query.filter_by(is_private=False)
    elif not current_user.is_admin:
        websites_query = websites_query.filter(
            (Website.is_private == False) |
            (Website.created_by_id == current_user.id) |
            (Website.visible_to.contains(str(current_user.id)))
        )
    
    websites = websites_query.all()
    return render_template('search.html', 
                         title='搜索结果', 
                         websites=websites, 
                         query=query)

@bp.route('/about')
def about():
    return render_template('about.html', title='关于我们')

@bp.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"websites": []})
    
    websites = Website.query.filter(Website.title.contains(query) | 
                                  Website.description.contains(query) | 
                                  Website.url.contains(query)).all()
    
    # 将网站对象转换为JSON格式
    websites_data = []
    for site in websites:
        category_data = None
        if site.category:
            category_data = {
                'id': site.category.id,
                'name': site.category.name,
                'icon': site.category.icon,
                'color': site.category.color
            }
            
        websites_data.append({
            'id': site.id,
            'title': site.title,
            'url': site.url,
            'description': site.description,
            'icon': site.icon,
            'category': category_data
        })
    
    return jsonify({"websites": websites_data})

@bp.route('/api/website/<int:site_id>/update', methods=['POST'])
@login_required
def update_website(site_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "未提供数据"}), 400
        
        site = Website.query.get_or_404(site_id)
        
        # 检查用户权限，只有管理员可以修改链接
        if not current_user.is_admin:
            return jsonify({"success": False, "message": "没有权限执行此操作"}), 403
        
        # 更新网站信息
        if 'title' in data:
            site.title = data['title']
        if 'url' in data:
            site.url = data['url']
        if 'icon' in data:
            site.icon = data['icon']
        if 'description' in data:
            site.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "网站信息已成功更新",
            "website": {
                "id": site.id,
                "title": site.title,
                "url": site.url,
                "icon": site.icon,
                "description": site.description
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"}), 500

@bp.route('/site/<int:site_id>/info')
def site_info(site_id):
    try:
        site = Website.query.get_or_404(site_id)
        
        category_data = None
        if site.category:
            category_data = {
                'id': site.category.id,
                'name': site.category.name,
                'icon': site.category.icon,
                'color': site.category.color
            }
            
        website_data = {
            'id': site.id,
            'title': site.title,
            'url': site.url,
            'description': site.description,
            'icon': site.icon,
            'category': category_data,
            'views': site.views,
            'is_private': site.is_private
        }
        
        return jsonify({"success": True, "website": website_data})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取失败: {str(e)}"}), 500

# 帮助解析网站信息的函数
def parse_website_info(url):
    try:
        # 添加超时和请求头以模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 确保请求成功
        
        # 检测网页编码
        content_type = response.headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1]
            response.encoding = charset
        else:
            # 尝试从网页内容中检测编码
            content = response.content
            soup = BeautifulSoup(content, 'html.parser')
            meta_charset = soup.find('meta', charset=True)
            if meta_charset:
                response.encoding = meta_charset.get('charset')
            else:
                meta_content_type = soup.find('meta', {'http-equiv': lambda x: x and x.lower() == 'content-type'})
                if meta_content_type and 'charset=' in meta_content_type.get('content', '').lower():
                    charset = meta_content_type.get('content').lower().split('charset=')[-1]
                    response.encoding = charset
                elif 'charset=gb' in response.text.lower() or 'charset="gb' in response.text.lower():
                    response.encoding = 'gb18030'
                else:
                    # 如果没有明确指定编码，尝试用 apparent_encoding
                    response.encoding = response.apparent_encoding
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取网站标题
        title = ""
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else ""
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
        
        # 提取描述信息
        description = ""
        meta_desc = soup.find('meta', attrs={'name': ['description', 'Description']})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content').strip()
        
        # 如果没有描述标签，提取页面的第一段有意义的文字作为描述
        if not description:
            # 尝试查找第一个非空的p标签
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text and len(text) > 20:  # 确保文本有一定长度
                    description = text
                    break
        
        # 如果描述太长，截断
        if description and len(description) > 200:
            description = description[:197] + "..."
            
        return {
            "success": True,
            "title": title,
            "description": description
        }
    except Exception as e:
        print(f"解析网站信息出错: {str(e)}")  # 添加错误日志
        return {
            "success": False,
            "message": str(e)
        }

@bp.route('/api/fetch_website_info')
def fetch_website_info():
    url = request.args.get('url', '')
    if not url:
        return jsonify({"success": False, "message": "未提供URL参数"})
    
    # 确保URL有协议前缀
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
        
    # 获取网站信息
    result = parse_website_info(url)
    return jsonify(result)

@bp.route('/api/website/update/<int:id>', methods=['POST'])
@login_required
def api_update_website(id):
    """更新网站链接的API接口"""
    # 检查当前用户是否为管理员
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取要修改的网站
    website = Website.query.get_or_404(id)
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    # 验证URL格式
    url = data.get('url')
    if not url or not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'message': 'URL格式不正确'}), 400
    
    # 更新网站URL
    website.url = url
    
    # 可选: 更新其他字段
    if 'title' in data:
        website.title = data['title']
    if 'description' in data:
        website.description = data['description']
    if 'icon' in data:
        website.icon = data['icon']
    if 'is_featured' in data and isinstance(data['is_featured'], bool):
        website.is_featured = data['is_featured']
    if 'category_id' in data and isinstance(data['category_id'], int):
        # 验证分类是否存在
        category = Category.query.get(data['category_id'])
        if category:
            website.category_id = data['category_id']
    if 'is_private' in data:
        website.is_private = bool(data['is_private'])
    
    # 保存更改
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': '网站信息更新成功',
        'website': {
            'id': website.id,
            'title': website.title,
            'url': website.url,
            'description': website.description,
            'icon': website.icon,
            'is_featured': website.is_featured,
            'category_id': website.category_id
        }
    })

@bp.route('/api/website/delete/<int:id>', methods=['POST', 'DELETE'])
@login_required
def api_delete_website(id):
    """删除网站链接的API接口"""
    # 检查当前用户是否为管理员
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    try:
        # 获取要删除的网站
        website = Website.query.get_or_404(id)
        
        # 临时保存网站标题用于返回消息
        website_title = website.title
        
        # 删除网站
        db.session.delete(website)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'网站"{website_title}"已成功删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@bp.route('/api/modify_link', methods=['POST'])
@login_required
def api_modify_link():
    """修改链接的API接口"""
    # 检查用户权限
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    if not data or 'url' not in data or not data['url']:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    # 获取要修改的网站
    website_id = data.get('id')
    if not website_id:
        return jsonify({'success': False, 'message': '未提供网站ID'}), 400
    
    try:
        website = Website.query.get_or_404(website_id)
        
        # 更新URL
        website.url = data['url']
        
        # 更新其他可选字段
        if 'title' in data and data['title']:
            website.title = data['title']
        if 'description' in data and data['description']:
            website.description = data['description']
        if 'icon' in data and data['icon']:
            website.icon = data['icon']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '链接已更新'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'}), 500

@bp.route('/api/website/update_order', methods=['POST'])
@login_required
@csrf.exempt
def update_website_order():
    """更新网站排序顺序的API接口"""
    # 检查当前用户是否为管理员
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    items = data['items']
    print(f"收到排序请求: {items}") # 记录排序数据
    
    try:
        # 更新每个网站的排序顺序
        updated_count = 0
        for item in items:
            website_id = item.get('id')
            sort_order = item.get('sort_order')
            
            if website_id is not None and sort_order is not None:
                website = Website.query.get(website_id)
                if website:
                    old_sort = website.sort_order
                    website.sort_order = sort_order
                    updated_count += 1
                    print(f"更新站点ID {website_id} 排序: {old_sort} -> {sort_order}")
        
        # 保存更改
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'排序顺序已更新 ({updated_count} 个站点)'
        })
    except Exception as e:
        db.session.rollback()
        print(f"排序更新失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新排序失败: {str(e)}'}), 500

@bp.route('/api/website/quick-add', methods=['POST'])
@login_required
def quick_add_website():
    """快速添加网站的API接口"""
    # 检查用户权限
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        # 验证必要字段
        required_fields = ['url', 'category_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 创建新网站
        website = Website(
            title=data.get('title', ''),
            url=data['url'],
            description=data.get('description', ''),
            icon=data.get('icon', ''),
            category_id=data['category_id'],
            created_by_id=current_user.id,
            sort_order=1,  # 新添加的链接权重为1
            is_private=data.get('is_private', 0)  # 默认为公开
        )
        
        db.session.add(website)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '网站添加成功',
            'website': {
                'id': website.id,
                'title': website.title,
                'url': website.url,
                'description': website.description,
                'icon': website.icon,
                'category_id': website.category_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500 