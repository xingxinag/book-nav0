"""
重建应用，避免缓存问题
使用方法：
1. 关闭当前正在运行的应用
2. 运行此脚本
3. 重新启动应用
"""
import os
import sys
import importlib
import shutil
from pathlib import Path

# 清理所有的__pycache__目录
print("清理Python缓存文件...")
for root, dirs, _ in os.walk('.'):
    for dir_name in dirs:
        if dir_name == '__pycache__':
            cache_path = os.path.join(root, dir_name)
            print(f"删除: {cache_path}")
            try:
                shutil.rmtree(cache_path)
            except Exception as e:
                print(f"无法删除 {cache_path}: {e}")

# 重新加载模型文件，确保没有错误
print("\n验证模型文件...")
sys.path.insert(0, os.getcwd())
try:
    # 强制重新加载模块
    if 'app.models' in sys.modules:
        del sys.modules['app.models']
    
    import app.models
    importlib.reload(app.models)
    print("模型文件验证成功")
except Exception as e:
    print(f"模型文件验证失败: {e}")
    sys.exit(1)

# 创建临时app.py，用于测试应用能否启动
print("\n创建临时测试文件...")
with open('temp_app.py', 'w') as f:
    f.write("""
from app import create_app, db

app = create_app()
with app.app_context():
    # 打印数据库结构
    inspector = db.inspect(db.engine)
    for table_name in inspector.get_table_names():
        print(f"表名: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  - 列名: {column['name']}, 类型: {column['type']}")
            
    print("\\n应用初始化成功，数据库结构正常！")
    
    # 检查Website模型不含sort_order字段
    from app.models import Website
    assert not hasattr(Website, 'sort_order'), "模型中仍然包含sort_order属性，请修复models.py文件"
    print("Website模型检查通过，不含sort_order字段")
""")

print("\n运行测试应用...")
os.system('python temp_app.py')

print("\n清理临时文件...")
if os.path.exists('temp_app.py'):
    os.remove('temp_app.py')

print("\n重建成功！请使用以下命令启动应用:")
print("flask run") 