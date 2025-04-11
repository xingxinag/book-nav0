from datetime import datetime
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from config import Config

# 定义网站和标签的多对多关系表
website_tag = db.Table('website_tag',
    db.Column('website_id', db.Integer, db.ForeignKey('website.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    websites = db.relationship('Website', backref='creator', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class InvitationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), index=True, unique=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    used_by = db.relationship('User', foreign_keys=[used_by_id])
    
    @staticmethod
    def generate_code():
        length = Config.INVITATION_CODE_LENGTH
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            if not InvitationCode.query.filter_by(code=code).first():
                return code
    
    def __repr__(self):
        return f'<InvitationCode {self.code}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(256))
    icon = db.Column(db.String(64))
    color = db.Column(db.String(16))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    websites = db.relationship('Website', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    url = db.Column(db.String(256))
    description = db.Column(db.String(512))
    icon = db.Column(db.String(256))
    views = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sort_order = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 私有链接相关字段
    is_private = db.Column(db.Boolean, default=False)
    visible_to = db.Column(db.String(512), default='')  # 存储可见用户ID，用逗号分隔
    
    # 统计相关字段
    views_today = db.Column(db.Integer, default=0)
    last_view = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Website {self.title}>'
        
    def is_visible_to(self, user):
        """检查链接是否对指定用户可见"""
        # 如果不是私有链接，对所有人可见
        if not self.is_private:
            return True
            
        # 如果是私有链接
        if user is None:  # 未登录用户
            return False
            
        # 创建者和管理员可见
        if user.is_admin or user.id == self.created_by_id:
            return True
            
        # 检查是否在可见用户列表中
        if self.visible_to:
            visible_user_ids = [int(id) for id in self.visible_to.split(',') if id]
            return user.id in visible_user_ids
            
        return False 