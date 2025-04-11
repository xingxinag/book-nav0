"""
直接修复Category表的脚本
这个脚本将直接在数据库中为Category表添加display_limit字段
"""
import os
import shutil
import sqlite3
from datetime import datetime

# 确保我们在正确的目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_ROOT)

# 1. 备份数据库
print("正在备份数据库...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"app_backup_{timestamp}.db"
shutil.copy2("app.db", backup_file)
print(f"数据库已备份为: {backup_file}")

# 2. 连接数据库
print("正在连接数据库...")
conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# 3. 检查category表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category'")
if cursor.fetchone():
    print("Category表存在")
    
    # 4. 检查display_limit字段是否已存在
    cursor.execute("PRAGMA table_info(category)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'display_limit' in columns:
        print("display_limit字段已存在")
    else:
        # 5. 添加display_limit字段
        print("正在添加display_limit字段...")
        try:
            cursor.execute("ALTER TABLE category ADD COLUMN display_limit INTEGER DEFAULT 8")
            conn.commit()
            print("已成功添加display_limit字段，默认值为8")
        except sqlite3.Error as e:
            print(f"添加字段时出错: {e}")
else:
    print("错误: Category表不存在!")

# 6. 清理数据库中的迁移版本信息
print("正在清理数据库中的迁移版本信息...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
if cursor.fetchone():
    # 检查当前的版本号
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    print(f"当前的迁移版本是: {version[0] if version else 'None'}")
    
    # 删除旧的迁移版本记录
    cursor.execute("DELETE FROM alembic_version")
    conn.commit()
    print("已清除alembic_version表中的所有记录")
else:
    print("alembic_version表不存在")

conn.close()

print("直接修复完成！")
print(f"如果有问题，可以恢复备份: {backup_file}")
print("现在应该可以正常运行 flask db init 和 flask db migrate 命令了") 