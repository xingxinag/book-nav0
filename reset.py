"""
重置应用，清理缓存文件，准备重新启动
"""
import os
import sys
import shutil
import importlib
from sqlalchemy import inspect, create_engine
from config import Config

# 删除所有__pycache__目录
def delete_pycache():
    print("删除Python缓存文件...")
    for root, dirs, _ in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                try:
                    path = os.path.join(root, d)
                    print(f"删除: {path}")
                    shutil.rmtree(path)
                except:
                    print(f"无法删除: {path}")

# 查看实际数据库结构
def check_database():
    print("\n检查数据库结构...")
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)
    
    # 检查website表结构
    if 'website' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('website')]
        print(f"Website表列: {columns}")
        
        # 检查是否存在sort_order列
        if 'sort_order' not in columns:
            print("数据库正常: Website表中不存在sort_order列")
        else:
            print("警告: Website表中存在sort_order列，但模型中已删除。这可能导致异常。")
    else:
        print("错误: 数据库中不存在website表")

# 主函数
def main():
    print("开始重置应用...")
    
    # 1. 删除缓存
    delete_pycache()
    
    # 2. 检查数据库
    check_database()
    
    # 3. 最终提示
    print("\n重置完成。请使用以下命令启动应用:")
    print("flask run")

if __name__ == "__main__":
    main() 