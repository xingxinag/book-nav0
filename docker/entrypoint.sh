#!/bin/sh
set -e

# 设置环境变量
export FLASK_APP=run.py
export DATABASE_URL="sqlite:////app/app.db"
export PREFERRED_URL_SCHEME="http"

echo "=== 容器启动 ==="

# 检查数据库目录
echo "创建必要目录..."
mkdir -p /app/app/backups /app/app/uploads /data/backups /data/uploads
chmod -R 777 /app/app/backups /app/app/uploads /data

# 检查宿主机数据库文件
if [ ! -f /data/app.db ]; then
    echo "宿主机数据库不存在，创建新数据库..."
    
    # 创建空数据库文件
    touch /app/app.db
    chmod 666 /app/app.db
    
    # 直接使用python脚本创建数据库
    cd /app
    python3 << EOF
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    db.create_all()
    # 创建默认管理员
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True, is_superadmin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账户创建成功")
EOF
    
    # 复制到宿主机
    cp /app/app.db /data/app.db
    echo "数据库初始化完成"
else
    echo "使用现有数据库..."
    cp /data/app.db /app/app.db
    chmod 666 /app/app.db
fi

# 确保数据库文件权限正确
chmod 666 /app/app.db
ls -la /app/app.db

echo "=== 启动应用服务 ==="
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf 