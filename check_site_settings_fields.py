import sqlite3

# 数据库文件名
DB_PATH = 'app.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(site_settings);")
columns = cursor.fetchall()

print("site_settings表字段：")
for col in columns:
    print(col[1])

fields = [
    'announcement_enabled',
    'announcement_title',
    'announcement_content',
    'announcement_link',
    'announcement_start',
    'announcement_end'
]

print("\n弹窗公告相关字段存在情况：")
for field in fields:
    exists = any(col[1] == field for col in columns)
    print(f"{field}: {'存在' if exists else '不存在'}")

conn.close() 