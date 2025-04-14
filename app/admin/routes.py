from datetime import datetime
from functools import wraps
import os
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, session, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db, csrf
from app.admin import bp
from app.admin.forms import CategoryForm, WebsiteForm, InvitationForm, UserEditForm, SiteSettingsForm
from app.models import Category, Website, InvitationCode, User, SiteSettings, OperationLog

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin:
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
            display_limit=form.display_limit.data,
            parent_id=form.parent_id.data
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
    
    # 修复初始选择
    if form.parent_id.data is None:
        form.parent_id.data = 0
        
    if form.validate_on_submit():
        # 检查是否尝试将分类设为自身的子分类或后代的子分类
        if form.parent_id.data and form.parent_id.data == id:
            flash('分类不能作为自身的子分类', 'danger')
            return render_template('admin/category_form.html', title='编辑分类', form=form)
            
        # 获取所有后代ID
        descendants = [c.id for c in category.get_all_descendants()] if hasattr(category, 'get_all_descendants') else []
        if form.parent_id.data in descendants:
            flash('分类不能设置为其后代分类的子分类', 'danger')
            return render_template('admin/category_form.html', title='编辑分类', form=form)
            
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
    per_page = request.args.get('per_page', 10, type=int)  # 从URL参数中获取每页显示数量
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
        
        try:
            # 记录添加操作
            category = Category.query.get(form.category_id.data) if form.category_id.data else None
            category_name = category.name if category else None
            
            operation_log = OperationLog(
                user_id=current_user.id,
                operation_type='ADD',
                website_id=website.id,
                website_title=website.title,
                website_url=website.url,
                website_icon=website.icon,
                category_id=website.category_id,
                category_name=category_name,
                details='{}'
            )
            db.session.add(operation_log)
            db.session.commit()
        except Exception as e:
            # 记录日志失败不影响主功能
            current_app.logger.error(f"记录添加操作日志失败: {str(e)}")
        
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
        try:
            # 记录修改前的状态
            old_title = website.title
            old_url = website.url
            old_description = website.description
            old_category_id = website.category_id
            old_category = Category.query.get(old_category_id) if old_category_id else None
            old_category_name = old_category.name if old_category else None
            old_is_featured = website.is_featured
            old_is_private = website.is_private
            
            # 更新网站信息
            form.populate_obj(website)
            # 处理私有/公开选项
            website.is_private = form.is_private.data
            db.session.commit()
            
            # 确定哪些字段发生了变化
            changes = {}
            if old_title != website.title:
                changes['title'] = {'old': old_title, 'new': website.title}
            if old_url != website.url:
                changes['url'] = {'old': old_url, 'new': website.url}
            if old_description != website.description:
                changes['description'] = {'old': old_description, 'new': website.description}
                
            if old_category_id != website.category_id:
                new_category = Category.query.get(website.category_id) if website.category_id else None
                new_category_name = new_category.name if new_category else None
                changes['category'] = {
                    'old': old_category_name, 
                    'new': new_category_name
                }
                
            if old_is_featured != website.is_featured:
                changes['is_featured'] = {'old': old_is_featured, 'new': website.is_featured}
            if old_is_private != website.is_private:
                changes['is_private'] = {'old': old_is_private, 'new': website.is_private}
            
            # 如果有变化，才记录修改操作
            if changes:
                import json
                operation_log = OperationLog(
                    user_id=current_user.id,
                    operation_type='MODIFY',
                    website_id=website.id,
                    website_title=website.title,
                    website_url=website.url,
                    website_icon=website.icon,
                    category_id=website.category_id,
                    category_name=new_category_name if 'category' in changes else (old_category_name or None),
                    details=json.dumps(changes)
                )
                db.session.add(operation_log)
                db.session.commit()
        except Exception as e:
            # 记录日志失败不影响主功能
            current_app.logger.error(f"记录修改操作日志失败: {str(e)}")
            # 确保网站信息已保存
            db.session.commit()
        
        flash('网站更新成功', 'success')
        return redirect(url_for('admin.websites'))
    return render_template('admin/website_form.html', title='编辑网站', form=form)

@bp.route('/website/delete/<int:id>')
@login_required
@admin_required
def delete_website(id):
    website = Website.query.get_or_404(id)
    
    # 记录删除操作
    import json
    details = {
        'description': website.description,
        'is_private': website.is_private,
        'is_featured': website.is_featured
    }
    
    operation_log = OperationLog(
        user_id=current_user.id,
        operation_type='DELETE',
        website_id=None,  # 删除后ID不存在
        website_title=website.title,
        website_url=website.url,
        website_icon=website.icon,
        category_id=website.category_id,
        category_name=website.category.name if website.category else None,
        details=json.dumps(details)
    )
    
    db.session.add(operation_log)
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
        # 使用URL参数传递消息而不是flash
        return redirect(url_for('admin.invitations', flash_message=f'成功生成{count}个邀请码', flash_category='success'))
    return redirect(url_for('admin.invitations'))

@bp.route('/invitation/delete/<int:id>')
@login_required
@admin_required
def delete_invitation(id):
    invitation = InvitationCode.query.get_or_404(id)
    if invitation.used_by_id is not None:
        # 使用URL参数传递错误消息
        return redirect(url_for('admin.invitations', flash_message='该邀请码已被使用，无法删除', flash_category='danger'))
    else:
        db.session.delete(invitation)
        db.session.commit()
        # 使用URL参数传递成功消息
        return redirect(url_for('admin.invitations', flash_message='邀请码删除成功', flash_category='success'))
    return redirect(url_for('admin.invitations'))

# 用户管理
@bp.route('/users')
@login_required
@superadmin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', title='用户管理', users=users)


@bp.route('/user/detail/<int:id>')
@login_required
@superadmin_required
def user_detail(id):
    user = User.query.get_or_404(id)
    websites = Website.query.filter_by(created_by_id=user.id).all()
    
    page_size = {
        'added': request.args.get('added_per_page', 10, type=int),
        'modified': request.args.get('modified_per_page', 10, type=int),
        'deleted': request.args.get('deleted_per_page', 10, type=int)
    }
    page = {
        'added': request.args.get('added_page', 1, type=int),
        'modified': request.args.get('modified_page', 1, type=int),
        'deleted': request.args.get('deleted_page', 1, type=int)
    }
    
    # 查询用户的操作记录
    added_records_query = OperationLog.query.filter_by(
        user_id=user.id, 
        operation_type='ADD'
    ).order_by(OperationLog.created_at.desc())
    
    modified_records_query = OperationLog.query.filter_by(
        user_id=user.id, 
        operation_type='MODIFY'
    ).order_by(OperationLog.created_at.desc())
    
    deleted_records_query = OperationLog.query.filter_by(
        user_id=user.id, 
        operation_type='DELETE'
    ).order_by(OperationLog.created_at.desc())
    
    # 使用分页
    added_pagination = added_records_query.paginate(
        page=page['added'], 
        per_page=page_size['added'],
        error_out=False
    )
    modified_pagination = modified_records_query.paginate(
        page=page['modified'], 
        per_page=page_size['modified'],
        error_out=False
    )
    deleted_pagination = deleted_records_query.paginate(
        page=page['deleted'], 
        per_page=page_size['deleted'],
        error_out=False
    )
    
    added_records = added_pagination.items
    modified_records = modified_pagination.items
    deleted_records = deleted_pagination.items
    
    return render_template(
        'admin/user_detail.html', 
        title='用户详情', 
        user=user, 
        websites=websites,
        added_records=added_records,
        modified_records=modified_records,
        deleted_records=deleted_records,
        added_pagination=added_pagination,
        modified_pagination=modified_pagination,
        deleted_pagination=deleted_pagination
    )


@bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserEditForm(user.username, user.email, obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        
        # 如果提供了新密码，则更新密码
        if form.password.data:
            user.set_password(form.password.data)
        
        # 只有超级管理员可以更改管理员权限，普通管理员不能改
        user.is_admin = form.is_admin.data
        # 超级管理员权限只有当前用户是超级管理员时才能赋予他人
        if current_user.is_superadmin and form.is_superadmin.data:
            user.is_superadmin = True
        
        db.session.commit()
        flash('用户信息更新成功!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_edit.html', title='编辑用户', form=form, user=user)

# 添加删除用户功能
@bp.route('/user/delete/<int:id>')
@login_required
@superadmin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户', 'danger')
        return redirect(url_for('admin.users'))
    
    # 删除前检查关联的网站，可以选择转移或删除
    websites_count = Website.query.filter_by(created_by_id=user.id).count()
    if websites_count > 0:
        flash(f'该用户已创建了 {websites_count} 个网站，请先处理这些内容', 'warning')
        return redirect(url_for('admin.user_detail', id=user.id))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'用户 {username} 已被删除', 'success')
    return redirect(url_for('admin.users'))

# 站点设置管理
@bp.route('/site-settings', methods=['GET', 'POST'])
@login_required
@superadmin_required
def site_settings():
    settings = SiteSettings.get_settings()
    form = SiteSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # 处理Logo上传
        if form.logo_file.data:
            logo_filename = save_image(form.logo_file.data, 'logos')
            if logo_filename:
                settings.site_logo = url_for('static', filename=f'uploads/logos/{logo_filename}')
        elif form.site_logo.data:
            settings.site_logo = form.site_logo.data
            
        # 处理Favicon上传
        if form.favicon_file.data:
            favicon_filename = save_image(form.favicon_file.data, 'favicons')
            if favicon_filename:
                settings.site_favicon = url_for('static', filename=f'uploads/favicons/{favicon_filename}')
        elif form.site_favicon.data:
            settings.site_favicon = form.site_favicon.data
            
        # 更新其他字段
        settings.site_name = form.site_name.data
        settings.site_subtitle = form.site_subtitle.data
        settings.site_keywords = form.site_keywords.data
        settings.site_description = form.site_description.data
        settings.footer_content = form.footer_content.data
        
        db.session.commit()
        flash('站点设置已更新', 'success')
        return redirect(url_for('admin.site_settings'))
        
    return render_template('admin/site_settings.html', title='站点设置', form=form, settings=settings)

def save_image(file_data, subfolder):
    """保存上传的图片到static/uploads目录"""
    if not file_data:
        return None
        
    # 确保存储目录存在
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名并保存文件
    filename = secure_filename(file_data.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        file_data.save(file_path)
        return unique_filename
    except Exception as e:
        flash(f'图片上传失败: {str(e)}', 'danger')
        return None 


# 处理操作日志相关API
@bp.route('/api/operation-log/delete', methods=['POST'])
@login_required
@admin_required
def delete_operation_log():
    data = request.json
    log_id = data.get('id')
    
    if not log_id:
        return jsonify({'success': False, 'message': '未提供日志ID'})
    
    log = OperationLog.query.get(log_id)
    if not log:
        return jsonify({'success': False, 'message': '日志不存在'})
    
    db.session.delete(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '日志删除成功'})

@bp.route('/api/operation-log/batch-delete', methods=['POST'])
@login_required
@admin_required
def batch_delete_operation_logs():
    data = request.json
    log_ids = data.get('ids', [])
    
    if not log_ids:
        return jsonify({'success': False, 'message': '未提供日志ID'})
    
    logs = OperationLog.query.filter(OperationLog.id.in_(log_ids)).all()
    for log in logs:
        db.session.delete(log)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'已删除 {len(logs)} 条日志'})
