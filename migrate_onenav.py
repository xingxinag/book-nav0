import sqlite3
import json
import os
import sys
from datetime import datetime
from flask import Flask
from app import create_app, db
from app.models import Category, Website, User

# 检查命令行参数
if len(sys.argv) < 2:
    print("使用方法: python migrate_onenav.py <数据库文件路径> [replace|merge]")
    print("参数说明:")
    print("  <数据库文件路径>: OneNav数据库文件的路径")
    print("  replace|merge: 导入模式，replace表示替换现有数据，merge表示合并数据（默认为merge）")
    sys.exit(1)

# 获取数据库路径和导入模式
db_path = sys.argv[1]
import_mode = sys.argv[2].lower() if len(sys.argv) > 2 else "merge"

if not os.path.exists(db_path):
    print(f"错误: 找不到数据库文件 '{db_path}'")
    sys.exit(1)

if import_mode not in ["replace", "merge"]:
    print(f"错误: 导入模式必须是 'replace' 或 'merge'")
    sys.exit(1)

# 配置应用
app = create_app()
app.app_context().push()

# 源数据库连接
try:
    source_conn = sqlite3.connect(db_path)
    source_conn.row_factory = sqlite3.Row
except Exception as e:
    print(f"错误: 无法连接到源数据库 - {str(e)}")
    sys.exit(1)

# 检查是否为OneNav数据库
def check_onenav_db():
    """检查是否为OneNav格式的数据库"""
    cursor = source_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='on_categorys' OR name='on_links'")
    tables = cursor.fetchall()
    table_names = [table['name'] for table in tables]
    
    if 'on_categorys' not in table_names or 'on_links' not in table_names:
        print("错误: 不是有效的OneNav数据库，缺少必要的表")
        return False
    return True

# 获取当前管理员用户ID
def get_admin_id():
    """获取管理员用户ID"""
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        print("错误: 系统中没有管理员用户")
        sys.exit(1)
    return admin.id

# 迁移配置
ADMIN_USER_ID = get_admin_id()

def get_categories():
    """从OneNav获取所有分类"""
    cursor = source_conn.cursor()
    cursor.execute("SELECT * FROM on_categorys ORDER BY weight DESC")
    return cursor.fetchall()

def get_links():
    """从OneNav获取所有链接"""
    cursor = source_conn.cursor()
    cursor.execute("SELECT * FROM on_links ORDER BY fid, weight DESC")
    return cursor.fetchall()

def migrate_categories():
    """迁移分类数据"""
    categories = get_categories()
    category_mapping = {}  # 存储旧ID到新ID的映射
    
    print(f"开始迁移分类，共{len(categories)}条...")
    
    # 获取现有分类（合并模式使用）
    existing_categories = {}
    if import_mode == "merge":
        existing_categories = {c.name.lower(): c for c in Category.query.all()}
    
    # 先处理一级分类
    for category in categories:
        if category['fid'] == 0:  # 一级分类
            # 检查合并模式下是否已存在同名分类
            cat_name = category['name'].lower()
            if import_mode == "merge" and cat_name in existing_categories:
                # 使用现有分类ID
                category_mapping[category['id']] = existing_categories[cat_name].id
                print(f"  合并一级分类: {category['name']} (ID: {category['id']} -> {existing_categories[cat_name].id})")
            else:
                # 创建新分类
                new_category = Category(
                    name=category['name'],
                    description=category['description'] or '',
                    icon=map_icon(category['font_icon']),
                    order=category['weight']
                )
                db.session.add(new_category)
                db.session.flush()  # 获取新ID
                
                # 保存ID映射关系
                category_mapping[category['id']] = new_category.id
                if import_mode == "merge":
                    existing_categories[cat_name] = new_category
                print(f"  {'新建' if import_mode == 'merge' else '迁移'}一级分类: {category['name']} (ID: {category['id']} -> {new_category.id})")
    
    # 再处理二级分类
    for category in categories:
        if category['fid'] != 0:  # 二级分类
            # 检查父分类是否已迁移
            if category['fid'] in category_mapping:
                # 检查合并模式下是否已存在同名分类
                cat_name = category['name'].lower()
                if import_mode == "merge" and cat_name in existing_categories:
                    # 使用现有分类ID
                    category_mapping[category['id']] = existing_categories[cat_name].id
                    print(f"  合并二级分类: {category['name']} (ID: {category['id']} -> {existing_categories[cat_name].id})")
                else:
                    # 创建新分类
                    new_category = Category(
                        name=category['name'],
                        description=category['description'] or '',
                        icon=map_icon(category['font_icon']),
                        order=category['weight'],
                        parent_id=category_mapping[category['fid']]
                    )
                    db.session.add(new_category)
                    db.session.flush()
                    
                    # 保存ID映射关系
                    category_mapping[category['id']] = new_category.id
                    if import_mode == "merge":
                        existing_categories[cat_name] = new_category
                    print(f"  {'新建' if import_mode == 'merge' else '迁移'}二级分类: {category['name']} (ID: {category['id']} -> {new_category.id})")
            else:
                print(f"  ⚠️ 跳过二级分类 {category['name']} (ID: {category['id']})，父分类ID {category['fid']} 未找到")
    
    db.session.commit()
    print(f"分类迁移完成，共迁移{len(category_mapping)}条")
    return category_mapping

def migrate_links(category_mapping):
    """迁移链接数据"""
    links = get_links()
    
    print(f"开始迁移链接，共{len(links)}条...")
    migrated_count = 0
    skipped_count = 0
    
    # 获取现有URL（合并模式使用）
    existing_urls = {}
    if import_mode == "merge":
        existing_urls = {w.url.lower(): True for w in Website.query.all()}
    
    for link in links:
        # 检查分类是否已迁移
        if link['fid'] in category_mapping:
            # 检查URL是否重复（合并模式）
            url_lower = link['url'].lower()
            if import_mode == "merge" and url_lower in existing_urls:
                skipped_count += 1
                print(f"  跳过重复链接: {link['title']} ({link['url']})")
                continue
                
            # 转换时间戳为datetime
            try:
                add_time = datetime.fromtimestamp(int(link['add_time']))
            except:
                add_time = datetime.now()
            
            try:
                new_website = Website(
                    title=link['title'],
                    url=link['url'],
                    description=link['description'] or '',
                    icon=link['font_icon'] or '',
                    category_id=category_mapping[link['fid']],
                    created_by_id=ADMIN_USER_ID,
                    created_at=add_time,
                    sort_order=link['weight'] or 0,
                    is_private=(link['property'] == 1),  # 假设property=1表示私有
                    views=link['click'] or 0
                )
                db.session.add(new_website)
                migrated_count += 1
                if import_mode == "merge":
                    existing_urls[url_lower] = True
                
                # 每100条提交一次，避免内存问题
                if migrated_count % 100 == 0:
                    db.session.commit()
                    print(f"  已迁移{migrated_count}条链接...")
            except Exception as e:
                skipped_count += 1
                print(f"  ⚠️ 链接导入出错 {link['title']}: {str(e)}")
        else:
            skipped_count += 1
            print(f"  ⚠️ 跳过链接 {link['title']} (ID: {link['id']})，分类ID {link['fid']} 未找到")
    
    # 最后提交剩余数据
    db.session.commit()
    print(f"链接迁移完成，成功: {migrated_count}条，跳过: {skipped_count}条")

def map_icon(font_icon):
    """将OneNav的图标格式转换为我们系统的格式"""
    # OneNav可能使用Font Awesome图标，例如"fa fa-book"
    # 如果是URL格式，则直接返回
    if font_icon and (font_icon.startswith('http://') or font_icon.startswith('https://')):
        return font_icon
    
    # 如果是Font Awesome图标，转换为Bootstrap图标
    fa_to_bs = {
        'fa-book': 'bi-book',
        'fa-android': 'bi-android',
        'fa-angellist': 'bi-list-stars',
        'fa-area-chart': 'bi-graph-up',
        'fa-video-camera': 'bi-camera-video',
        # 可以根据需要添加更多映射
    }
    
    if font_icon:
        for fa, bs in fa_to_bs.items():
            if fa in font_icon:
                return bs
    
    # 默认图标
    return 'bi-link'

def main():
    """主迁移函数"""
    print(f"开始OneNav数据迁移（模式：{import_mode}）...")
    print(f"源数据库: {db_path}")
    
    # 检查数据库格式
    if not check_onenav_db():
        sys.exit(1)
    
    # 如果是替换模式，清空现有数据
    if import_mode == "replace":
        print("执行替换模式，将清空现有数据...")
        Website.query.delete()
        Category.query.delete()
        db.session.commit()
        print("现有数据已清空")
    
    # 1. 迁移分类
    category_mapping = migrate_categories()
    
    # 2. 迁移链接
    if category_mapping:
        migrate_links(category_mapping)
    
    # 关闭连接
    source_conn.close()
    
    print("OneNav数据迁移完成!")

if __name__ == "__main__":
    main() 