#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复用户头像显示问题脚本
"""

import os
import sqlite3
import sys
from pathlib import Path

def fix_avatar_paths():
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    # 获取实际存在的头像文件列表
    avatar_dir = Path('app/static/uploads/avatars')
    if not avatar_dir.exists():
        print(f"头像目录不存在: {avatar_dir}")
        return False
    
    # 获取真实存在的头像文件
    existing_avatars = list(avatar_dir.glob('*.png')) + list(avatar_dir.glob('*.jpg')) + list(avatar_dir.glob('*.gif'))
    if not existing_avatars:
        print("头像目录中没有找到图片文件")
        return False
    
    print(f"在{avatar_dir}目录中找到{len(existing_avatars)}个头像文件:")
    for avatar in existing_avatars:
        print(f" - {avatar.name}")
    
    # 连接数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询有头像的用户
        cursor.execute("SELECT id, username, avatar FROM user WHERE avatar IS NOT NULL")
        users = cursor.fetchall()
        
        if not users:
            print("没有用户设置了头像")
            conn.close()
            return False
        
        print(f"\n找到{len(users)}个设置了头像的用户:")
        
        # 更新用户头像路径
        updated_count = 0
        for user_id, username, avatar_url in users:
            print(f"\n用户: {username}")
            print(f"当前头像URL: {avatar_url}")
            
            # 检查当前URL指向的文件是否存在
            if avatar_url.startswith('/static/'):
                file_path = Path('app') / avatar_url[1:]  # 移除开头的'/'
                if file_path.exists():
                    print(f"✅ 文件已存在，无需更新: {file_path}")
                    continue
            
            # 当前头像文件不存在，尝试匹配新文件
            print("❌ 当前头像文件不存在，尝试寻找匹配的文件...")
            
            # 获取用户ID部分的文件名，例如 "xxx_1_yyy.png" 中的 "_1_"
            user_id_pattern = f"_{user_id}_"
            matching_files = [f for f in existing_avatars if user_id_pattern in f.name]
            
            if matching_files:
                # 使用最新的匹配文件
                latest_file = max(matching_files, key=lambda f: os.path.getmtime(f))
                new_url = f"/static/uploads/avatars/{latest_file.name}"
                cursor.execute("UPDATE user SET avatar = ? WHERE id = ?", (new_url, user_id))
                print(f"✅ 找到匹配文件，已更新头像URL: {new_url}")
                updated_count += 1
            else:
                # 没有匹配的文件，使用任意最新的头像文件
                print("⚠️ 未找到与用户ID匹配的文件，使用最新的头像文件")
                latest_file = max(existing_avatars, key=lambda f: os.path.getmtime(f))
                new_url = f"/static/uploads/avatars/{latest_file.name}"
                cursor.execute("UPDATE user SET avatar = ? WHERE id = ?", (new_url, user_id))
                print(f"✅ 已更新头像URL: {new_url}")
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        if updated_count > 0:
            print(f"\n成功更新了{updated_count}个用户的头像路径。请重新登录测试头像显示。")
        else:
            print("\n没有需要更新的头像路径。")
        
        return True
    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始修复用户头像路径问题...\n")
    fix_avatar_paths() 