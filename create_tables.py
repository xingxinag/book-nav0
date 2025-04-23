from app import create_app, db
from app.models import DeadlinkCheck, Website
from sqlalchemy import inspect, Column, Boolean, DateTime
import sqlite3

app = create_app()

def check_and_create_tables():
    with app.app_context():
        # 获取SQLite连接
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查Website表是否有需要的字段
        cursor.execute("PRAGMA table_info(website)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # 如果Website表缺少is_valid字段，添加它
        if 'is_valid' not in column_names:
            print("添加 is_valid 字段到 Website 表...")
            cursor.execute("ALTER TABLE website ADD COLUMN is_valid BOOLEAN DEFAULT 1")
        
        # 如果Website表缺少last_check字段，添加它
        if 'last_check' not in column_names:
            print("添加 last_check 字段到 Website 表...")
            cursor.execute("ALTER TABLE website ADD COLUMN last_check TIMESTAMP")
        
        # 检查DeadlinkCheck表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deadlink_check'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("创建 DeadlinkCheck 表...")
            # 创建DeadlinkCheck表
            cursor.execute("""
            CREATE TABLE deadlink_check (
                id INTEGER PRIMARY KEY,
                check_id VARCHAR(36),
                website_id INTEGER NOT NULL,
                url VARCHAR(256) NOT NULL,
                is_valid BOOLEAN DEFAULT 1,
                status_code INTEGER,
                error_type VARCHAR(50),
                error_message TEXT,
                response_time FLOAT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (website_id) REFERENCES website (id)
            )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX idx_deadlink_check_check_id ON deadlink_check (check_id)")
            cursor.execute("CREATE INDEX idx_deadlink_check_website_id ON deadlink_check (website_id)")
        
        # 提交更改
        conn.commit()
        conn.close()
        
        print("数据库更新完成！")

if __name__ == "__main__":
    check_and_create_tables() 