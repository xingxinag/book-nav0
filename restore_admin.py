#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
恢复管理员权限脚本

1. 检查数据库表结构
2. 恢复admin用户的超级管理员权限
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

def inspect_db():
    """检查数据库结构"""
    db_path = 'app.db'
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 列出所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info("数据库中的表:")
        for table in tables:
            logger.info(f"- {table[0]}")
        
        # 查看user表结构
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        logger.info("\nuser表结构:")
        for col in columns:
            logger.info(f"- {col[1]} ({col[2]})")
        
        # 检查用户信息
        cursor.execute("SELECT id, username, is_admin, is_superadmin FROM user")
        users = cursor.fetchall()
        logger.info("\n用户列表:")
        for user in users:
            logger.info(f"- ID: {user[0]}, 用户名: {user[1]}, 管理员: {user[2]}, 超级管理员: {user[3]}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"检查数据库时出错: {str(e)}")
        return False

def restore_admin():
    """恢复admin用户的超级管理员权限"""
    db_path = 'app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查找admin用户
        cursor.execute("SELECT id, username, is_admin, is_superadmin FROM user WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            logger.error("未找到admin用户!")
            conn.close()
            return False
        
        logger.info(f"找到admin用户 (ID: {admin[0]}), 当前权限: 管理员={admin[2]}, 超级管理员={admin[3]}")
        
        # 恢复权限
        cursor.execute("UPDATE user SET is_admin = 1, is_superadmin = 1 WHERE username = 'admin'")
        conn.commit()
        
        # 验证更新
        cursor.execute("SELECT is_admin, is_superadmin FROM user WHERE username = 'admin'")
        updated = cursor.fetchone()
        logger.info(f"权限更新后: 管理员={updated[0]}, 超级管理员={updated[1]}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"恢复管理员权限时出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== 开始检查数据库 ===")
    if inspect_db():
        logger.info("\n=== 开始恢复admin权限 ===")
        if restore_admin():
            logger.info("\n√ 管理员权限恢复成功!")
        else:
            logger.error("\n✗ 管理员权限恢复失败!")
    else:
        logger.error("\n✗ 数据库检查失败!") 