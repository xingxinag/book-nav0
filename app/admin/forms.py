from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField, HiddenField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError, Email, EqualTo
from app.models import Category, User

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('分类描述', validators=[Length(max=256)])
    icon = StringField('图标类名', validators=[Length(max=64)])
    color = StringField('颜色代码', validators=[Length(max=16)])
    order = IntegerField('排序顺序', default=0)
    display_limit = IntegerField('首页展示数量', default=8, 
                               validators=[DataRequired()])
    parent_id = SelectField('父级分类', coerce=int, validators=[Optional()])
    submit = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, '-- 无父级分类（作为顶级分类） --')] + [
            (c.id, c.name) for c in Category.query.filter_by(parent_id=None).order_by(Category.order).all()
        ]
        
    def validate_parent_id(self, field):
        if field.data == 0:
            field.data = None

class WebsiteForm(FlaskForm):
    title = StringField('网站名称', validators=[DataRequired(), Length(max=128)])
    url = StringField('网站URL', validators=[DataRequired(), URL(), Length(max=256)])
    description = TextAreaField('网站描述', validators=[Length(max=512)])
    icon = StringField('图标URL', validators=[Length(max=256)])
    category_id = SelectField('所属分类', coerce=int, validators=[DataRequired()])
    is_featured = BooleanField('设为推荐')
    is_private = BooleanField('设为私有')
    submit = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(WebsiteForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.order).all()]

class InvitationForm(FlaskForm):
    count = IntegerField('生成数量', default=1)
    submit = SubmitField('生成邀请码')

class UserEditForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('邮箱', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('新密码', validators=[Optional(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[Optional(), EqualTo('password')])
    is_admin = BooleanField('管理员权限')
    submit = SubmitField('保存更改')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('该用户名已被使用，请选择其他用户名。')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('该邮箱已被注册，请使用其他邮箱。')

class SiteSettingsForm(FlaskForm):
    site_name = StringField('网站标题', validators=[DataRequired(), Length(max=128)])
    site_logo = StringField('网站Logo URL', validators=[Optional(), Length(max=256)])
    logo_file = FileField('上传Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'gif', 'svg'], '只允许上传图片文件')
    ])
    site_favicon = StringField('网站图标 URL', validators=[Optional(), Length(max=256)])
    favicon_file = FileField('上传图标', validators=[
        Optional(),
        FileAllowed(['ico', 'png', 'jpg'], '只允许上传图标文件')
    ])
    site_subtitle = StringField('网站副标题', validators=[Optional(), Length(max=256)])
    site_keywords = StringField('网站关键词', validators=[Optional(), Length(max=512)])
    site_description = TextAreaField('网站描述', validators=[Optional(), Length(max=1024)])
    footer_content = TextAreaField('自定义页脚', validators=[Optional()])
    submit = SubmitField('保存设置') 