import sqlite3
import os
from datetime import datetime

# 假设数据库文件在项目根目录
db_path = "app.db"

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"错误: 数据库文件 {db_path} 不存在!")
    exit(1)

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表是否已存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_settings'")
if cursor.fetchone():
    print("site_settings表已存在，跳过创建")
else:
    # 创建site_settings表
    cursor.execute("""
    CREATE TABLE site_settings (
        id INTEGER PRIMARY KEY,
        site_name VARCHAR(128) DEFAULT '炫酷导航',
        site_logo VARCHAR(256),
        site_favicon VARCHAR(256),
        site_subtitle VARCHAR(256),
        site_keywords VARCHAR(512),
        site_description VARCHAR(1024),
        footer_content TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 创建一条初始记录
    cursor.execute("""
    INSERT INTO site_settings (
        site_name, updated_at
    ) VALUES (?, ?)
    """, ('炫酷导航', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    print("site_settings表创建成功，并添加了初始记录")

# 提交更改并关闭连接
conn.commit()
conn.close()

print("操作完成") 