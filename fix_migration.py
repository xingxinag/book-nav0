"""
修复数据库迁移问题的脚本
这个脚本将执行以下操作：
1. 备份当前数据库
2. 重新初始化迁移系统
3. 创建初始迁移和包含display_limit字段的迁移
"""
import os
import shutil
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

# 2. 删除现有的迁移文件夹
print("正在清理迁移文件...")
migrations_dir = os.path.join(APP_ROOT, "migrations")
if os.path.exists(migrations_dir):
    print("删除整个migrations目录...")
    shutil.rmtree(migrations_dir)
    print("已删除migrations目录")

# 3. 重新初始化迁移系统
print("正在重新初始化迁移...")
subprocess.run(["flask", "db", "init"])
print("迁移系统已重新初始化")

# 4. 创建初始迁移
print("正在创建初始迁移...")
subprocess.run(["flask", "db", "migrate", "-m", "初始化迁移"])

# 5. 升级数据库
print("正在应用迁移...")
subprocess.run(["flask", "db", "upgrade"])

print("迁移修复完成！")
print(f"如果有问题，可以恢复备份: {backup_file}") 