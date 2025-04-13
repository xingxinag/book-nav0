import os
import sys
import sqlite3

# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 获取数据库文件路径
db_path = os.path.join(root_dir, 'app.db')
# 获取SQL迁移文件路径
sql_path = os.path.join(root_dir, 'migrations', 'add_parent_id.sql')

def execute_migration():
    """执行SQL迁移文件"""
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        sys.exit(1)
        
    # 读取SQL文件内容
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except Exception as e:
        print(f"读取SQL文件失败: {e}")
        sys.exit(1)
        
    # 连接数据库并执行SQL
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查parent_id列是否已存在
        cursor.execute("PRAGMA table_info(category)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'parent_id' in column_names:
            print("parent_id列已存在，跳过迁移")
            return
            
        # 执行SQL脚本
        cursor.executescript(sql_script)
        conn.commit()
        
        print("数据库迁移成功执行")
    except Exception as e:
        print(f"执行SQL迁移失败: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    execute_migration() 