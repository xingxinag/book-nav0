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
    avatar = db.Column(db.String(255))  # 用户头像字段
    is_admin = db.Column(db.Boolean, default=False)
    is_superadmin = db.Column(db.Boolean, default=False)  # 超级管理员标识
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
    display_limit = db.Column(db.Integer, default=10)  # 首页展示数量限制，默认为10个
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 添加父分类关系
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # 关系定义
    children = db.relationship('Category', 
                              backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic')
    websites = db.relationship('Website', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
        
    def get_ancestors(self):
        """获取所有祖先分类，从直接父级到顶级"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]  # 逆序返回，从顶级到直接父级
    
    def is_descendant_of(self, category_id):
        """检查当前分类是否是指定分类的后代"""
        if self.parent_id is None:
            return False
        if self.parent_id == category_id:
            return True
        return self.parent.is_descendant_of(category_id)
    
    def get_all_descendants(self):
        """获取所有后代分类（递归）"""
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_descendants())
        return result


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


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(128), default="炫酷导航")
    site_logo = db.Column(db.String(256), nullable=True)  # 存储logo图片URL
    site_favicon = db.Column(db.String(256), nullable=True)  # 存储网站图标URL
    site_subtitle = db.Column(db.String(256), nullable=True)
    site_keywords = db.Column(db.String(512), nullable=True)
    site_description = db.Column(db.String(1024), nullable=True)
    footer_content = db.Column(db.Text, nullable=True)  # 自定义页脚内容
    background_image = db.Column(db.String(512), nullable=True)  # 旧字段，保留以确保兼容性
    enable_background = db.Column(db.Boolean, default=False)  # 旧字段，保留以确保兼容性
    background_type = db.Column(db.String(32), default='none')  # 背景类型：none, image, gradient, color
    background_url = db.Column(db.String(512), nullable=True)  # 背景图片URL或颜色值
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 单例模式：确保只有一条记录
    @classmethod
    def get_settings(cls):
        """获取站点设置（单例模式）"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<SiteSettings {self.site_name}>'


class Background(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))  # 背景名称
    url = db.Column(db.String(512))  # 背景URL
    type = db.Column(db.String(32))  # 背景类型：image, gradient, color
    device_type = db.Column(db.String(32))  # 设备类型：pc, mobile, both
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship('User', backref='backgrounds')
    
    def __repr__(self):
        return f'<Background {self.title}>'


class OperationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    operation_type = db.Column(db.String(50))  # ADD, MODIFY, DELETE
    website_id = db.Column(db.Integer, nullable=True)  # 可以为空，表示记录已被删除的网站
    website_title = db.Column(db.String(128), nullable=True)
    website_url = db.Column(db.String(256), nullable=True)
    website_icon = db.Column(db.String(256), nullable=True)
    category_id = db.Column(db.Integer, nullable=True)
    category_name = db.Column(db.String(64), nullable=True)
    details = db.Column(db.Text, nullable=True)  # 存储更多操作细节，JSON格式
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='operations')
    
    def __repr__(self):
        return f'<OperationLog {self.operation_type} {self.website_title}>'
