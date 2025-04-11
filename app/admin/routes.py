from datetime import datetime
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from app import db, csrf
from app.admin import bp
from app.admin.forms import CategoryForm, WebsiteForm, InvitationForm
from app.models import Category, Website, InvitationCode, User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    stats = {
        'users': User.query.count(),
        'active_users': User.query.filter(User.created_at > datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).count(),
        'categories': Category.query.count(),
        'websites': Website.query.count(),
        'invitation_codes': InvitationCode.query.filter_by(is_active=True, used_by_id=None).count()
    }
    return render_template('admin/index.html', title='管理面板', stats=stats)

# 分类管理
@bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.order.asc()).all()
    return render_template('admin/categories.html', title='分类管理', categories=categories)

@bp.route('/category/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data,
            color=form.color.data,
            order=form.order.data,
            display_limit=form.display_limit.data
        )
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', title='添加分类', form=form)

@bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('分类更新成功', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', title='编辑分类', form=form)

@bp.route('/category/delete/<int:id>')
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if Website.query.filter_by(category_id=id).first():
        flash('该分类下存在网站，无法删除', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类删除成功', 'success')
    return redirect(url_for('admin.categories'))

# 网站管理
@bp.route('/websites')
@login_required
@admin_required
def websites():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示的数量
    category_id = request.args.get('category_id', type=int)
    
    # 构建查询
    query = Website.query
    
    # 应用分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 获取分页数据
    pagination = query.order_by(Website.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    websites = pagination.items
    
    # 获取所有分类供筛选使用
    categories = Category.query.order_by(Category.order.asc()).all()
    
    return render_template(
        'admin/websites.html',
        title='网站管理',
        websites=websites,
        pagination=pagination,
        categories=categories
    )

@bp.route('/api/website/batch-delete', methods=['POST'])
@login_required
@admin_required
@csrf.exempt  # 豁免CSRF保护
def batch_delete_websites():
    """批量删除网站"""
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
            
        website_ids = data['ids']
        if not isinstance(website_ids, list):
            return jsonify({'success': False, 'message': '无效的ID列表'}), 400
            
        # 删除选中的网站
        deleted_count = Website.query.filter(Website.id.in_(website_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个网站'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@bp.route('/api/website/batch-update', methods=['POST'])
@login_required
@admin_required
@csrf.exempt  # 豁免CSRF保护
def batch_update_websites():
    """批量更新网站"""
    try:
        data = request.get_json()
        if not data or 'ids' not in data or 'data' not in data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
            
        website_ids = data['ids']
        update_data = data['data']
        
        if not isinstance(website_ids, list):
            return jsonify({'success': False, 'message': '无效的ID列表'}), 400
            
        # 更新选中的网站
        websites = Website.query.filter(Website.id.in_(website_ids)).all()
        updated_count = 0
        for website in websites:
            if 'is_private' in update_data:
                website.is_private = update_data['is_private']
                updated_count += 1
                
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 个网站'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

@bp.route('/website/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_website():
    form = WebsiteForm()
    if form.validate_on_submit():
        website = Website(
            title=form.title.data,
            url=form.url.data,
            description=form.description.data,
            icon=form.icon.data,
            category_id=form.category_id.data,
            is_featured=form.is_featured.data,
            is_private=form.is_private.data,
            created_by_id=current_user.id,
            sort_order=1  # 新链接权重设为1（最小值）
        )
        db.session.add(website)
        db.session.commit()
        flash('网站添加成功', 'success')
        return redirect(url_for('admin.websites'))
    return render_template('admin/website_form.html', title='添加网站', form=form)

@bp.route('/website/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_website(id):
    website = Website.query.get_or_404(id)
    form = WebsiteForm(obj=website)
    if form.validate_on_submit():
        form.populate_obj(website)
        # 处理私有/公开选项
        website.is_private = form.is_private.data
        db.session.commit()
        flash('网站更新成功', 'success')
        return redirect(url_for('admin.websites'))
    return render_template('admin/website_form.html', title='编辑网站', form=form)

@bp.route('/website/delete/<int:id>')
@login_required
@admin_required
def delete_website(id):
    website = Website.query.get_or_404(id)
    db.session.delete(website)
    db.session.commit()
    flash('网站删除成功', 'success')
    return redirect(url_for('admin.websites'))

# 邀请码管理
@bp.route('/invitations')
@login_required
@admin_required
def invitations():
    active_codes = InvitationCode.query.filter_by(is_active=True, used_by_id=None).all()
    used_codes = InvitationCode.query.filter(InvitationCode.used_by_id.isnot(None)).all()
    form = InvitationForm()
    return render_template('admin/invitations.html', title='邀请码管理', 
                           active_codes=active_codes, used_codes=used_codes, form=form)

@bp.route('/invitation/generate', methods=['POST'])
@login_required
@admin_required
def generate_invitation():
    form = InvitationForm()
    if form.validate_on_submit():
        count = min(form.count.data, 10)  # 限制一次最多生成10个
        for _ in range(count):
            code = InvitationCode(
                code=InvitationCode.generate_code(),
                created_by_id=current_user.id
            )
            db.session.add(code)
        db.session.commit()
        flash(f'成功生成{count}个邀请码', 'success')
    return redirect(url_for('admin.invitations'))

@bp.route('/invitation/delete/<int:id>')
@login_required
@admin_required
def delete_invitation(id):
    invitation = InvitationCode.query.get_or_404(id)
    if invitation.used_by_id is not None:
        flash('该邀请码已被使用，无法删除', 'danger')
    else:
        db.session.delete(invitation)
        db.session.commit()
        flash('邀请码删除成功', 'success')
    return redirect(url_for('admin.invitations'))

# 用户管理
@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', title='用户管理', users=users) 