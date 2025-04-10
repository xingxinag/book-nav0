import sqlite3
import os

# SQL命令
sql_commands = [
    "ALTER TABLE website ADD COLUMN sort_order INTEGER DEFAULT 0;",
    "UPDATE website SET sort_order = id * 10;"
]

# 执行SQL
try:
    # 连接数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 执行每条SQL命令
    for cmd in sql_commands:
        try:
            cursor.execute(cmd)
            print(f"执行SQL成功: {cmd}")
        except sqlite3.OperationalError as e:
            # 如果列已存在，忽略错误
            if "duplicate column name" in str(e):
                print(f"列已存在，跳过: {cmd}")
            else:
                print(f"SQL执行错误: {e} - {cmd}")
    
    # 提交更改
    conn.commit()
    print("数据库更新成功!")
    
    # 查询验证
    cursor.execute("PRAGMA table_info(website)")
    columns = cursor.fetchall()
    print("\n网站表结构:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - 默认值: {col[4]}")
    
    # 关闭连接
    conn.close()
    
except Exception as e:
    print(f"发生错误: {e}") 