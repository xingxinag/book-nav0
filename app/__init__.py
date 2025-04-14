from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
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
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin:
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                email=app.config['ADMIN_EMAIL'],
                is_admin=True,
                is_superadmin=True  # 设置初始管理员为超级管理员
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
        elif admin.is_admin and not admin.is_superadmin:
            # 确保现有管理员也是超级管理员
            admin.is_superadmin = True
            db.session.commit()
    
    return app

from app import models 