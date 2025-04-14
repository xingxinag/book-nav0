#!/usr/bin/env python
"""
添加is_superadmin字段到用户表并设置现有管理员为超级管理员
"""
import os
import sys
import sqlite3
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import inspect

# 获取Flask应用实例
def get_app():
    from app import create_app
    return create_app()

def add_superadmin_field():
    """检查并添加is_superadmin字段，设置管理员为超级管理员"""
    print("开始检查和添加超级管理员字段...")
    
    try:
        # 获取Flask应用
        app = get_app()
        
        # 在应用上下文中执行
        with app.app_context():
            from app import db
            from app.models import User
            
            # 检查字段是否存在
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            field_exists = 'is_superadmin' in columns
            
            if field_exists:
                print("字段 'is_superadmin' 已存在，无需添加。")
            else:
                print("字段 'is_superadmin' 不存在，将进行添加...")
                
                # 使用SQLite直接添加字段
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                
                print(f"数据库路径: {db_path}")
                
                # 连接数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 添加字段
                cursor.execute("ALTER TABLE user ADD COLUMN is_superadmin BOOLEAN DEFAULT 0")
                conn.commit()
                
                print("成功添加 'is_superadmin' 字段")
                
                # 关闭连接
                cursor.close()
                conn.close()
            
            # 将所有管理员设置为超级管理员
            print("正在设置现有管理员为超级管理员...")
            admin_count = 0
            
            for user in User.query.filter_by(is_admin=True).all():
                if not hasattr(user, 'is_superadmin') or not user.is_superadmin:
                    user.is_superadmin = True
                    admin_count += 1
                    print(f"设置用户 '{user.username}' 为超级管理员")
            
            if admin_count > 0:
                db.session.commit()
                print(f"成功将 {admin_count} 个管理员设置为超级管理员")
            else:
                print("没有找到需要更新的管理员")
            
            print("操作完成!")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_superadmin_field()
    sys.exit(0 if success else 1) 