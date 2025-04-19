import os
import sys
import sqlite3
from datetime import datetime

# 数据库文件路径
DB_PATH = 'app.db'  # 修改为您实际的数据库文件路径

def add_transition_fields():
    """添加新的过渡页相关字段到site_settings表"""
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_settings'")
        if not cursor.fetchone():
            print("Error: site_settings表不存在!")
            return False
        
        # 检查字段是否已经存在
        cursor.execute("PRAGMA table_info(site_settings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 需要添加的字段
        new_fields = [
            {"name": "transition_remember_choice", "type": "BOOLEAN", "default": "1"},
            {"name": "transition_show_description", "type": "BOOLEAN", "default": "1"},
            {"name": "transition_theme", "type": "VARCHAR(32)", "default": "'default'"},
            {"name": "transition_color", "type": "VARCHAR(32)", "default": "'#6e8efb'"}
        ]
        
        # 添加缺失的字段
        for field in new_fields:
            if field["name"] not in columns:
                sql = f"ALTER TABLE site_settings ADD COLUMN {field['name']} {field['type']} DEFAULT {field['default']}"
                print(f"执行: {sql}")
                cursor.execute(sql)
                print(f"已添加字段: {field['name']}")
            else:
                print(f"字段已存在，跳过: {field['name']}")
        
        # 提交更改
        conn.commit()
        print("所有字段添加完成!")
        
        # 检查当前所有字段
        cursor.execute("PRAGMA table_info(site_settings)")
        print("\n当前site_settings表的所有字段:")
        for column in cursor.fetchall():
            print(f"{column[0]}: {column[1]} ({column[2]})")
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始向site_settings表添加新字段...")
    success = add_transition_fields()
    if success:
        print("脚本执行成功!")
    else:
        print("脚本执行失败!") 