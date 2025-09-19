from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, URL, Length, Optional, NumberRange

class SearchForm(FlaskForm):
    """搜索表单"""
    query = StringField('搜索', validators=[DataRequired()])
    submit_btn = SubmitField('搜索')

class WebsiteForm(FlaskForm):
    """添加/编辑网站表单"""
    title = StringField('网站名称', validators=[DataRequired(), Length(max=128)])
    url = StringField('网站URL', validators=[DataRequired(), URL(), Length(max=256)])
    description = TextAreaField('网站描述', validators=[Optional(), Length(max=512)])
    icon = StringField('图标URL', validators=[Optional(), Length(max=256)])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    sort_order = IntegerField('排序权重', validators=[Optional(), NumberRange(min=0, max=9999)], 
                            default=0, description='值越大排序越靠前，默认为0')
    is_private = BooleanField('设为私有')
    submit_btn = SubmitField('提交') 