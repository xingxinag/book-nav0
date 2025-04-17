#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
背景管理数据库迁移脚本
完成以下任务:
1. 检查并添加 SiteSettings 表中的背景相关字段
2. 创建 Background 表
3. 添加示例背景数据
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 数据库文件路径，默认为当前目录下的app.db
DB_PATH = 'app.db'

def check_db_exists():
    """检查数据库文件是否存在"""
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件 {DB_PATH} 不存在！")
        return False
    logger.info(f"找到数据库文件: {DB_PATH}")
    return True

def get_column_names(conn, table_name):
    """获取指定表的所有列名"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [column[1] for column in columns]

def check_table_exists(conn, table_name):
    """检查表是否存在"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def create_backup(db_path):
    """创建数据库备份"""
    from shutil import copyfile
    backup_path = f"{db_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        copyfile(db_path, backup_path)
        logger.info(f"已创建数据库备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

def add_background_fields_to_site_settings(conn):
    """向SiteSettings表添加背景相关字段"""
    cursor = conn.cursor()
    
    # 检查表是否存在
    if not check_table_exists(conn, 'site_settings'):
        logger.error("SiteSettings表不存在！")
        return False
    
    # 获取当前列
    columns = get_column_names(conn, 'site_settings')
    logger.info(f"当前site_settings表列: {columns}")
    
    # 检查是否需要添加新字段
    if 'background_type' in columns and 'background_url' in columns:
        logger.info("背景字段已存在，无需修改")
        return True
    
    # SQLite不支持直接添加多个列，需要创建新表并复制数据
    logger.info("使用表重建方法添加背景字段...")
    
    try:
        # 1. 获取当前表结构
        cursor.execute("PRAGMA table_info(site_settings)")
        table_info = cursor.fetchall()
        
        # 2. 生成建表语句
        create_table_sql = "CREATE TABLE site_settings_new (\n"
        for col in table_info:
            col_id, col_name, col_type, not_null, default_value, is_pk = col
            create_table_sql += f"    {col_name} {col_type}"
            
            if not_null:
                create_table_sql += " NOT NULL"
                
            if default_value is not None:
                create_table_sql += f" DEFAULT {default_value}"
                
            if is_pk:
                create_table_sql += " PRIMARY KEY"
                
            create_table_sql += ",\n"
        
        # 添加新列
        if 'background_type' not in columns:
            create_table_sql += "    background_type VARCHAR(32) DEFAULT 'none',\n"
        if 'background_url' not in columns:
            create_table_sql += "    background_url VARCHAR(512) NULL,\n"
        
        # 移除最后的逗号
        create_table_sql = create_table_sql.rstrip(",\n") + "\n)"
        
        # 3. 创建新表
        logger.info("创建临时表...")
        cursor.execute(create_table_sql)
        
        # 4. 复制数据
        logger.info("复制数据到临时表...")
        columns_str = ", ".join(columns)
        cursor.execute(f"INSERT INTO site_settings_new ({columns_str}) SELECT {columns_str} FROM site_settings")
        
        # 5. 删除旧表
        logger.info("删除旧表...")
        cursor.execute("DROP TABLE site_settings")
        
        # 6. 重命名新表
        logger.info("重命名新表为site_settings...")
        cursor.execute("ALTER TABLE site_settings_new RENAME TO site_settings")
        
        # 确认字段是否添加成功
        new_columns = get_column_names(conn, 'site_settings')
        logger.info(f"修改后site_settings表列: {new_columns}")
        
        added_fields = []
        if 'background_type' in new_columns:
            added_fields.append('background_type')
        if 'background_url' in new_columns:
            added_fields.append('background_url')
        
        if len(added_fields) == 0:
            logger.error("验证失败：没有字段被添加到site_settings表")
            return False
            
        conn.commit()
        logger.info(f"SiteSettings表更新完成，添加了字段: {', '.join(added_fields)}")
        return True
        
    except Exception as e:
        logger.error(f"修改表结构时出错: {str(e)}")
        conn.rollback()
        return False

def create_background_table(conn):
    """创建Background表"""
    cursor = conn.cursor()
    
    # 检查表是否已存在
    if check_table_exists(conn, 'background'):
        logger.info("Background表已存在")
        return True
    
    logger.info("创建Background表...")
    cursor.execute('''
    CREATE TABLE background (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(128) NOT NULL,
        url VARCHAR(512) NOT NULL,
        type VARCHAR(32) NOT NULL,
        device_type VARCHAR(32) NOT NULL,
        created_by_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_id) REFERENCES user (id)
    )
    ''')
    
    conn.commit()
    logger.info("Background表创建成功")
    return True

def add_sample_backgrounds(conn):
    """添加示例背景数据"""
    cursor = conn.cursor()
    
    # 检查是否已有背景数据
    cursor.execute("SELECT COUNT(*) FROM background")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Background表已有{count}条数据，跳过添加示例数据")
        return True
    
    # 获取admin用户ID
    cursor.execute("SELECT id FROM user WHERE username='admin' LIMIT 1")
    admin_id = cursor.fetchone()
    
    if admin_id:
        admin_id = admin_id[0]
    else:
        admin_id = 1  # 默认使用ID为1的用户
    
    # 示例背景数据
    sample_backgrounds = [
        ('紫蓝渐变', 'linear-gradient(135deg, #6e8efb, #a777e3)', 'gradient', 'both', admin_id),
        ('粉红渐变', 'linear-gradient(135deg, #f093fb, #f5576c)', 'gradient', 'both', admin_id),
        ('青绿渐变', 'linear-gradient(135deg, #5ee7df, #b490ca)', 'gradient', 'both', admin_id),
        ('淡蓝色', '#e3f2fd', 'color', 'both', admin_id),
        ('淡紫色', '#ede7f6', 'color', 'both', admin_id),
        ('淡绿色', '#e8f5e9', 'color', 'both', admin_id)
    ]
    
    # 插入示例数据
    for bg in sample_backgrounds:
        cursor.execute('''
        INSERT INTO background (title, url, type, device_type, created_by_id)
        VALUES (?, ?, ?, ?, ?)
        ''', bg)
    
    conn.commit()
    logger.info(f"成功添加{len(sample_backgrounds)}条示例背景数据")
    return True

def check_foreign_key_constraint(conn):
    """检查外键约束是否启用"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys")
    enabled = cursor.fetchone()[0]
    
    if not enabled:
        logger.warning("数据库外键约束未启用，正在启用...")
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        logger.info("外键约束已启用")
    else:
        logger.info("数据库外键约束已启用")
    
    return True

def main():
    """主函数"""
    logger.info("开始执行背景管理数据库迁移脚本...")
    
    # 检查数据库是否存在
    if not check_db_exists():
        return False
    
    # 创建备份
    if not create_backup(DB_PATH):
        if input("备份创建失败，是否继续? (y/n): ").lower() != 'y':
            return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        
        # 启用外键约束
        check_foreign_key_constraint(conn)
        
        # 添加背景字段到SiteSettings表
        if not add_background_fields_to_site_settings(conn):
            logger.error("添加背景字段到SiteSettings表失败")
            return False
        
        # 创建Background表
        if not create_background_table(conn):
            logger.error("创建Background表失败")
            return False
        
        # 添加示例背景数据
        if not add_sample_backgrounds(conn):
            logger.error("添加示例背景数据失败")
            return False
        
        # 检查创建的表结构
        logger.info("检查创建的Background表结构...")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(background)")
        for col in cursor.fetchall():
            logger.info(f"列: {col}")
        
        logger.info("背景管理数据库迁移完成！")
        return True
    
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 