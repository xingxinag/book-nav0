#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
临时脚本：检查用户头像问题
"""

import os
import sqlite3
import sys
from urllib.parse import urlparse
import requests

# 连接数据库
def check_user_avatars():
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询有头像的用户
        cursor.execute("SELECT id, username, avatar FROM user WHERE avatar IS NOT NULL")
        users = cursor.fetchall()
        
        if not users:
            print("没有用户设置了头像")
            return False
        
        print(f"\n找到 {len(users)} 个设置了头像的用户：")
        
        for user_id, username, avatar in users:
            print(f"\n用户ID: {user_id}")
            print(f"用户名: {username}")
            print(f"头像URL: {avatar}")
            
            # 分析URL
            parsed_url = urlparse(avatar)
            print(f"URL分析: {parsed_url}")
            
            # 检查本地文件是否存在
            if parsed_url.path.startswith('/static/'):
                file_path = os.path.join('app', parsed_url.path[1:])  # 去掉开头的'/'
                print(f"本地文件路径: {file_path}")
                if os.path.exists(file_path):
                    print("✅ 本地文件存在")
                else:
                    print("❌ 本地文件不存在")
            else:
                print("URL不是/static/开头，无法检查本地文件")
        
        # 建议
        print("\n可能的问题原因：")
        print("1. URL路径格式不正确 (期望 /static/uploads/avatars/filename.jpg)")
        print("2. 文件保存路径与URL路径不一致")
        print("3. Flask的static文件夹配置与代码中使用的不一致")
        
        print("\n建议解决方案：")
        print("1. 确认app/static目录是否正确配置为Flask的静态文件夹")
        print("2. 检查URL的生成方式是否与文件的实际存储位置匹配")
        print("3. 尝试修改avatar存储路径，确保与url_for生成的路径一致")
        
        conn.close()
        return True
    except Exception as e:
        print(f"检查过程中出错: {str(e)}")
        return False

# 创建简单的修复脚本
def fix_avatars_path():
    """尝试修复头像路径"""
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询有头像的用户
        cursor.execute("SELECT id, username, avatar FROM user WHERE avatar IS NOT NULL")
        users = cursor.fetchall()
        
        if not users:
            print("没有用户设置了头像")
            return False
        
        # 修复路径
        for user_id, username, avatar in users:
            if avatar and '/uploads/avatars/' in avatar:
                # 从路径中提取文件名
                filename = os.path.basename(avatar)
                # 创建新路径
                new_path = f"/static/uploads/avatars/{filename}"
                
                cursor.execute("UPDATE user SET avatar = ? WHERE id = ?", (new_path, user_id))
                print(f"已修复用户 {username} 的头像路径: {avatar} -> {new_path}")
        
        conn.commit()
        conn.close()
        print("\n修复完成。请重新登录测试头像显示。")
        return True
    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("检查用户头像信息...")
    if check_user_avatars():
        choice = input("\n是否尝试修复头像路径问题？(y/n): ")
        if choice.lower() == 'y':
            fix_avatars_path()
    else:
        print("检查失败") 