from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import datetime
import json
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 应用 ProxyFix 中间件 (信任直接连接的 Nginx 代理)
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    from app.models import User, InvitationCode, Category, Website, SiteSettings
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 添加全局上下文处理器
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    @app.context_processor
    def inject_site_settings():
        try:
            settings = SiteSettings.get_settings()
            return {'settings': settings}
        except Exception as e:
            # 记录错误，但返回一个空的设置对象，避免模板渲染失败
            print(f"无法获取站点设置: {str(e)}")
            # 创建一个临时设置对象，包含基本默认值
            default_settings = type('DefaultSettings', (), {
                'site_name': '炫酷导航',
                'site_logo': None,
                'site_favicon': None,
                'site_subtitle': '',
                'site_keywords': '',
                'site_description': '',
                'footer_content': None
            })
            return {'settings': default_settings}
    
    @app.before_first_request
    def create_admin():
        try:
            admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
            if not admin:
                # 尝试查找邮箱，防止email冲突
                admin_by_email = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
                if admin_by_email:
                    # 已有邮箱相同的用户，但用户名不是默认管理员
                    print(f"警告: 已存在邮箱为 {app.config['ADMIN_EMAIL']} 的用户，跳过创建默认管理员")
                    return
                
                # 创建新管理员
                admin = User(
                    username=app.config['ADMIN_USERNAME'],
                    email=app.config['ADMIN_EMAIL'],
                    is_admin=True,
                    is_superadmin=True
                )
                admin.set_password(app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()
                print("默认管理员账户创建成功")
            elif admin.is_admin and not admin.is_superadmin:
                # 确保现有管理员也是超级管理员
                admin.is_superadmin = True
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"创建/更新管理员账户时出错: {str(e)}")
    
    # 注册模板过滤器
    @app.template_filter('from_json')
    def from_json(value):
        try:
            return json.loads(value) if value else {}
        except:
            return {}
    
    @app.template_filter('boolstr')
    def boolstr(value):
        return '是' if value else '否'
    
    return app

from app import models 