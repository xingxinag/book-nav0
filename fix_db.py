"""
修复数据库中的迁移问题的脚本
这个脚本将直接修改数据库中的alembic_version表，清除旧的迁移记录
"""
import os
import shutil
import sqlite3
import subprocess
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

# 2. 清理数据库中的迁移版本信息
print("正在清理数据库中的迁移版本信息...")
conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# 检查alembic_version表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
if cursor.fetchone():
    # 删除旧的迁移版本记录
    cursor.execute("DELETE FROM alembic_version")
    conn.commit()
    print("已清除alembic_version表中的所有记录")
else:
    # 创建alembic_version表
    cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
    conn.commit()
    print("已创建新的alembic_version表")

conn.close()

# 3. 删除现有的迁移文件夹
print("正在清理迁移文件...")
migrations_dir = os.path.join(APP_ROOT, "migrations")
if os.path.exists(migrations_dir):
    print("删除整个migrations目录...")
    shutil.rmtree(migrations_dir)
    print("已删除migrations目录")

# 4. 重新初始化迁移系统
print("正在重新初始化迁移...")
subprocess.run(["flask", "db", "init"])
print("迁移系统已重新初始化")

# 5. 创建初始迁移
print("正在创建初始迁移...")
subprocess.run(["flask", "db", "migrate", "-m", "初始化迁移"])

# 6. 升级数据库
print("正在应用迁移...")
subprocess.run(["flask", "db", "upgrade"])

print("迁移修复完成！")
print(f"如果有问题，可以恢复备份: {backup_file}")
print("现在应该可以正常运行 flask db migrate -m \"Add display_limit field to Category model\" 了") 