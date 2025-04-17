#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户头像字段检查与添加脚本

1. 检查用户表是否有avatar字段
2. 如果没有则添加
3. 创建头像上传目录
"""

import os
import sys
import sqlite3
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_and_add_avatar_field():
    """检查并添加avatar字段"""
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查user表是否存在avatar字段
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        has_avatar = 'avatar' in columns
        logger.info(f"检查avatar字段: {'已存在' if has_avatar else '不存在'}")
        
        if not has_avatar:
            logger.info("添加avatar字段到user表...")
            try:
                # 添加avatar字段
                cursor.execute('ALTER TABLE user ADD COLUMN avatar VARCHAR(255)')
                conn.commit()
                logger.info("成功添加avatar字段")
            except Exception as e:
                logger.error(f"添加字段失败: {str(e)}")
                conn.close()
                return False
        
        # 创建avatars目录
        avatar_dir = os.path.join('app', 'static', 'uploads', 'avatars')
        if not os.path.exists(avatar_dir):
            logger.info(f"创建头像目录: {avatar_dir}")
            os.makedirs(avatar_dir, exist_ok=True)
        else:
            logger.info(f"头像目录已存在: {avatar_dir}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"操作过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    if check_and_add_avatar_field():
        logger.info("头像字段检查与添加完成")
    else:
        logger.error("操作失败") 