from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError
from app.models import Category

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('分类描述', validators=[Length(max=256)])
    icon = StringField('图标类名', validators=[Length(max=64)])
    color = StringField('颜色代码', validators=[Length(max=16)])
    order = IntegerField('排序顺序', default=0)
    submit = SubmitField('提交')

class WebsiteForm(FlaskForm):
    title = StringField('网站名称', validators=[DataRequired(), Length(max=128)])
    url = StringField('网站URL', validators=[DataRequired(), URL(), Length(max=256)])
    description = TextAreaField('网站描述', validators=[Length(max=512)])
    icon = StringField('图标URL', validators=[Length(max=256)])
    category_id = SelectField('所属分类', coerce=int, validators=[DataRequired()])
    is_featured = BooleanField('设为推荐')
    submit = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(WebsiteForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.order).all()]

class InvitationForm(FlaskForm):
    count = IntegerField('生成数量', default=1)
    submit = SubmitField('生成邀请码') 