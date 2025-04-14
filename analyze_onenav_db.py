import sqlite3
import json
import os
from pprint import pprint

# 连接到OneNav数据库
db_path = 'onenav_202503110959_1.1.2.db3'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def get_table_names():
    """获取数据库中的所有表名"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    return [table['name'] for table in tables]

def get_table_structure(table_name):
    """获取表结构"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [{'name': col['name'], 'type': col['type']} for col in columns]

def get_sample_data(table_name, limit=5):
    """获取表的示例数据"""
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_record_count(table_name):
    """获取表的记录数量"""
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    return cursor.fetchone()['count']

def analyze_database():
    """分析整个数据库结构和数据分布"""
    tables = get_table_names()
    db_structure = {}
    
    print(f"找到{len(tables)}个表:")
    for table_name in tables:
        print(f"\n表: {table_name}")
        
        # 获取表结构
        structure = get_table_structure(table_name)
        print("表结构:")
        for col in structure:
            print(f"  - {col['name']} ({col['type']})")
        
        # 获取记录数
        count = get_record_count(table_name)
        print(f"记录数: {count}")
        
        # 获取示例数据
        if count > 0:
            sample_data = get_sample_data(table_name)
            print("示例数据:")
            for i, row in enumerate(sample_data):
                print(f"  行 {i+1}:")
                for key, value in row.items():
                    print(f"    {key}: {value}")
        
        # 保存到结构对象
        db_structure[table_name] = {
            'structure': structure,
            'record_count': count
        }
    
    return db_structure

def suggest_migration_plan(db_structure):
    """根据分析结果建议迁移方案"""
    print("\n\n=== 数据迁移建议 ===")
    
    # 检查是否有链接和分类表
    has_links = False
    has_categories = False
    links_table = None
    categories_table = None
    
    for table_name, info in db_structure.items():
        # 启发式判断链接表
        columns = [col['name'].lower() for col in info['structure']]
        if 'url' in columns and ('title' in columns or 'name' in columns):
            has_links = True
            links_table = table_name
            print(f"发现链接表: {table_name}, 记录数: {info['record_count']}")
        
        # 启发式判断分类表
        if ('category' in table_name.lower() or 'cat' in table_name.lower()) and info['record_count'] > 0:
            has_categories = True
            categories_table = table_name
            print(f"发现分类表: {table_name}, 记录数: {info['record_count']}")
    
    if has_links and has_categories:
        print("\n✅ 可以迁移! 建议迁移步骤:")
        print("1. 先迁移分类数据到我们系统的Category表")
        print("2. 再迁移链接数据到我们系统的Website表，建立与分类的关联")
        print("3. 如果有用户数据，考虑迁移到我们系统的User表")
    elif has_links:
        print("\n⚠️ 部分可行! 发现链接数据但未找到分类数据，可以:")
        print("1. 创建默认分类")
        print("2. 将所有链接导入到默认分类下")
    else:
        print("\n❌ 迁移困难! 未发现足够的表结构来支持迁移")

if __name__ == "__main__":
    print(f"分析数据库: {db_path}")
    db_structure = analyze_database()
    suggest_migration_plan(db_structure)
    
    # 关闭连接
    conn.close()
    
    print("\n分析完成!") 