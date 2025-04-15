from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField, HiddenField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError, Email, EqualTo, NumberRange
from app.models import Category, User

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('分类描述', validators=[Length(max=256)])
    icon = StringField('图标', validators=[Length(max=64)])
    color = StringField('颜色', validators=[Length(max=16)])
    order = IntegerField('排序', default=0)
    display_limit = IntegerField('首页展示数量', default=10)
    parent_id = SelectField('父分类', coerce=int, validators=[Optional()])
    submit_btn = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, '-- 无 --')] + [
            (c.id, c.name) for c in Category.query.filter(Category.parent_id.is_(None)).all()
        ]
        
    def validate_parent_id(self, field):
        if field.data == 0:
            field.data = None

class WebsiteForm(FlaskForm):
    """添加/编辑网站表单"""
    title = StringField('网站名称', validators=[DataRequired(), Length(max=128)])
    url = StringField('网站URL', validators=[DataRequired(), URL(), Length(max=256)])
    description = TextAreaField('网站描述', validators=[Optional(), Length(max=512)])
    icon = StringField('图标URL', validators=[Optional(), Length(max=256)])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    sort_order = IntegerField('排序权重', validators=[Optional(), NumberRange(min=0, max=9999)], 
                            default=0, description='值越大排序越靠前，默认为0')
    is_featured = BooleanField('推荐')
    is_private = BooleanField('设为私有')
    submit_btn = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(WebsiteForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.order.asc()).all()]

class InvitationForm(FlaskForm):
    count = IntegerField('生成数量', default=1, validators=[DataRequired()])
    submit_btn = SubmitField('生成邀请码')

class UserEditForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('电子邮箱', validators=[DataRequired(), Email(), Length(max=120)])
    password = StringField('密码 (留空则不修改)', validators=[Optional(), Length(min=8, max=150)])
    is_admin = BooleanField('管理员权限')
    is_superadmin = BooleanField('超级管理员权限')
    submit_btn = SubmitField('保存')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('该用户名已被使用')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('该邮箱已被使用')

class SiteSettingsForm(FlaskForm):
    site_name = StringField('站点名称', validators=[DataRequired(), Length(max=128)])
    site_subtitle = StringField('站点副标题', validators=[Optional(), Length(max=256)])
    site_logo = StringField('站点Logo URL', validators=[Optional(), Length(max=256)])
    logo_file = FileField('上传Logo', validators=[FileAllowed(['jpg', 'png', 'gif', 'svg'], '只允许上传图片!')])
    site_favicon = StringField('站点图标URL', validators=[Optional(), Length(max=256)])
    favicon_file = FileField('上传Favicon', validators=[FileAllowed(['ico', 'png', 'jpg', 'svg'], '只允许上传图片!')])
    site_keywords = StringField('站点关键词', validators=[Optional(), Length(max=512)])
    site_description = TextAreaField('站点描述', validators=[Optional(), Length(max=1024)])
    footer_content = TextAreaField('页脚内容', validators=[Optional()])
    submit_btn = SubmitField('保存设置')

class DataImportForm(FlaskForm):
    """数据导入表单"""
    db_file = FileField('数据库文件', validators=[
        DataRequired(),
        FileAllowed(['db', 'db3', 'sqlite', 'sqlite3'], '只允许上传SQLite数据库文件')
    ])
    import_type = SelectField('导入类型', choices=[
        ('merge', '合并 - 保留现有数据'),
        ('replace', '替换 - 清空现有数据')
    ])
    submit_btn = SubmitField('开始导入') 