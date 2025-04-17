from datetime import datetime, timezone, timedelta
from functools import wraps
import os
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, session, current_app, send_file, send_from_directory
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from app import db, csrf
from app.admin import bp
from app.admin.forms import CategoryForm, WebsiteForm, InvitationForm, UserEditForm, SiteSettingsForm, DataImportForm, BackgroundForm
from app.models import Category, Website, InvitationCode, User, SiteSettings, OperationLog, Background
from app.main.routes import get_website_icon
import time
import json
import threading
from queue import Queue
from urllib.parse import urlparse
import requests
import shutil
import sqlite3
import tempfile
import random
import uuid
import secrets
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, func, desc, extract, case
from sqlalchemy.exc import SQLAlchemyError

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
    categories = Category.query.order_by(Category.order.desc()).all()
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
            sort_order=form.sort_order.data,  # 使用表单中的排序权重
            created_by_id=current_user.id
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
        # 记录修改前的值
        old_title = website.title
        old_url = website.url
        old_description = website.description
        old_category_id = website.category_id
        old_category_name = website.category.name if website.category else None
        old_is_featured = website.is_featured
        old_is_private = website.is_private
        old_sort_order = website.sort_order
        
        # 更新数据
        website.title = form.title.data
        website.url = form.url.data
        website.description = form.description.data
        website.icon = form.icon.data
        website.category_id = form.category_id.data
        website.is_featured = form.is_featured.data
        website.is_private = form.is_private.data
        website.sort_order = form.sort_order.data
        
        db.session.commit()
        
        # 记录修改操作
        changes = {}
        if old_title != website.title:
            changes['title'] = {'old': old_title, 'new': website.title}
        if old_url != website.url:
            changes['url'] = {'old': old_url, 'new': website.url}
        if old_description != website.description:
            changes['description'] = {'old': old_description, 'new': website.description}
        if old_category_id != website.category_id:
            new_category_name = website.category.name if website.category else None
            changes['category'] = {
                'old': {'id': old_category_id, 'name': old_category_name}, 
                'new': {'id': website.category_id, 'name': new_category_name}
            }
        if old_is_featured != website.is_featured:
            changes['is_featured'] = {'old': old_is_featured, 'new': website.is_featured}
        if old_is_private != website.is_private:
            changes['is_private'] = {'old': old_is_private, 'new': website.is_private}
        if old_sort_order != website.sort_order:
            changes['sort_order'] = {'old': old_sort_order, 'new': website.sort_order}
        
        if changes:  # 仅当有变更时才记录
            import json
            # 获取分类名称
            category = Category.query.get(form.category_id.data) if form.category_id.data else None
            category_name = category.name if category else None
            
            try:
                # 创建操作日志
                operation_log = OperationLog(
                    user_id=current_user.id,
                    operation_type='MODIFY',
                    website_id=website.id,
                    website_title=website.title,
                    website_url=website.url,
                    website_icon=website.icon,
                    category_id=website.category_id,
                    category_name=category_name,
                    details=json.dumps(changes)
                )
                db.session.add(operation_log)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"记录修改操作日志失败: {str(e)}")
        
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
@admin_required
def edit_user(id):
    """编辑用户"""
    user = User.query.get_or_404(id)
    
    # 普通管理员不能编辑超级管理员
    if user.is_superadmin and not current_user.is_superadmin:
        flash('权限不足，无法编辑超级管理员', 'danger')
        return redirect(url_for('admin.users'))
    
    # 创建表单并使用用户数据进行预填充
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
        
        # 处理头像上传
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            # 确保文件名安全
            filename = secure_filename(avatar_file.filename)
            # 添加时间戳避免文件名冲突
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            avatar_filename = f"{timestamp}_{user.id}_{filename}"
            
            # 确保avatars目录存在
            avatar_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存文件
            avatar_path = os.path.join(avatar_dir, avatar_filename)
            try:
                avatar_file.save(avatar_path)
                # 更新用户头像URL
                user.avatar = url_for('static', filename=f'uploads/avatars/{avatar_filename}')
                flash('头像已更新', 'success')
            except Exception as e:
                flash(f'头像上传失败: {str(e)}', 'danger')
        
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
    try:
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
            elif not form.site_logo.data and 'clear_logo' in request.form:
                # 清空Logo
                settings.site_logo = None
                
            # 处理Favicon上传
            if form.favicon_file.data:
                favicon_filename = save_image(form.favicon_file.data, 'favicons')
                if favicon_filename:
                    settings.site_favicon = url_for('static', filename=f'uploads/favicons/{favicon_filename}')
            elif form.site_favicon.data:
                settings.site_favicon = form.site_favicon.data
            elif not form.site_favicon.data and 'clear_favicon' in request.form:
                # 清空Favicon
                settings.site_favicon = None
                
            # 处理背景上传
            if form.background_file.data and form.background_type.data == 'image':
                bg_filename = save_image(form.background_file.data, 'backgrounds')
                if bg_filename:
                    settings.background_url = url_for('static', filename=f'uploads/backgrounds/{bg_filename}')
            elif form.background_url.data:
                settings.background_url = form.background_url.data
                
            # 更新其他字段
            settings.site_name = form.site_name.data
            settings.site_subtitle = form.site_subtitle.data
            settings.site_keywords = form.site_keywords.data
            settings.site_description = form.site_description.data
            settings.footer_content = form.footer_content.data
            settings.background_type = form.background_type.data
            
            try:
                db.session.commit()
                flash('站点设置已更新', 'success')
                return redirect(url_for('admin.site_settings'))
            except Exception as e:
                db.session.rollback()
                flash(f'保存设置失败: {str(e)}', 'danger')
                current_app.logger.error(f"保存站点设置失败: {str(e)}")
                
        return render_template('admin/site_settings.html', title='站点设置', form=form, settings=settings)
    except Exception as e:
        flash(f'加载站点设置失败: {str(e)}', 'danger')
        current_app.logger.error(f"加载站点设置失败: {str(e)}")
        return redirect(url_for('admin.index'))

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

# 数据库导入导出
import io
import shutil
import sqlite3
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
from app.admin.forms import DataImportForm

@bp.route('/data-management')
@login_required
@superadmin_required
def data_management():
    """数据管理页面"""
    import_form = DataImportForm()
    return render_template('admin/data_management.html', title='数据管理', import_form=import_form)

@bp.route('/export-data')
@login_required
@superadmin_required
def export_data():
    """导出数据库"""
    # 获取导出格式，默认为本项目格式
    export_format = request.args.get('format', 'native')
    
    # 确定时间戳
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    if export_format == 'onenav':
        filename = f"booknav_export_onenav_{timestamp}.db3"
    else:
        filename = f"booknav_export_{timestamp}.db3"
    
    # 创建临时文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db3')
    temp_db_path = temp_db.name
    temp_db.close()
    
    try:
        # 复制当前数据库
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        current_app.logger.info(f"准备从 {db_path} 导出数据到 {temp_db_path}")
        
        # 数据库路径可能是相对路径，需要转换为绝对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.root_path, db_path)
            current_app.logger.info(f"转换为绝对路径: {db_path}")
        
        # 检查源文件是否存在
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"找不到数据库文件: {db_path}")
        
        # 复制数据库文件
        shutil.copy2(db_path, temp_db_path)
        current_app.logger.info(f"数据库文件已复制")
        
        # 如果选择OneNav格式，则进行格式转换
        if export_format == 'onenav':
            current_app.logger.info("将导出转换为OneNav格式")
            if not convert_to_onenav_format(temp_db_path):
                raise Exception("转换为OneNav格式失败")
        
        # 读取临时文件的内容
        with open(temp_db_path, 'rb') as f:
            db_data = f.read()
            
        # 删除临时文件
        os.unlink(temp_db_path)
        
        # 将数据返回为可下载的文件
        current_app.logger.info(f"数据导出成功，大小：{len(db_data)}字节")
        return send_file(
            io.BytesIO(db_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        current_app.logger.error(f"导出数据失败: {str(e)}")
        # 确保临时文件被删除
        if os.path.exists(temp_db_path):
            try:
                os.unlink(temp_db_path)
            except:
                pass
        flash(f'导出数据失败: {str(e)}', 'danger')
        return redirect(url_for('admin.data_management'))

@bp.route('/import-data', methods=['POST'])
@login_required
@superadmin_required
def import_data():
    """导入数据库"""
    form = DataImportForm()
    if form.validate_on_submit():
        db_file = form.db_file.data
        import_type = form.import_type.data
        
        # 检查文件是否存在
        if not db_file:
            flash('请选择要导入的数据库文件', 'danger')
            return redirect(url_for('admin.data_management'))
        
        # 创建临时文件保存上传内容
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db3')
        temp_db_path = temp_db.name
        temp_db.close()
        
        try:
            # 保存上传的文件
            db_file.save(temp_db_path)
            
            # 在导入前先创建一个备份（安全措施）
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"pre_import_backup_{timestamp}.db3"
            backup_dir = os.path.join(current_app.root_path, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 复制当前数据库作为备份
            db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(current_app.root_path, db_path)
            shutil.copy2(db_path, backup_path)
            current_app.logger.info(f"已创建数据库备份: {backup_path}")
            
            # 自动检测数据库格式
            if is_project_db(temp_db_path):
                # 如果是本项目数据库格式
                current_app.logger.info("检测到本项目数据库格式")
                success, cat_count, link_count = import_project_db(temp_db_path, import_type, current_user.id)
                if success:
                    flash(f'数据导入成功! 导入了{cat_count}个分类和{link_count}个链接', 'success')
                else:
                    flash('数据导入失败', 'danger')
            elif is_onenav_db(temp_db_path):
                # 如果是OneNav格式
                current_app.logger.info("检测到OneNav数据库格式")
                
                # 如果是替换模式，清空现有数据
                if import_type == "replace":
                    current_app.logger.info("执行替换模式，清空现有数据...")
                    Website.query.delete()
                    Category.query.delete()
                    db.session.commit()
                
                try:
                    results = import_onenav_direct(temp_db_path, import_type, current_user.id)
                    flash(f'导入成功! {results["cats_count"]}个分类, {results["links_count"]}个链接', 'success')
                except Exception as e:
                    flash(f'导入过程中发生错误: {str(e)}', 'danger')
                    current_app.logger.error(f"导入错误: {str(e)}")
            else:
                # 如果格式无法识别
                flash('无法识别的数据库格式', 'danger')
                
            # 删除临时文件
            os.unlink(temp_db_path)
                
        except Exception as e:
            flash(f'数据导入失败: {str(e)}', 'danger')
            current_app.logger.error(f"数据导入失败: {str(e)}")
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
                
        return redirect(url_for('admin.data_management'))
        
    # 验证失败
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            
    return redirect(url_for('admin.data_management'))

def import_onenav_direct(db_path, import_type, admin_id):
    """直接导入OneNav数据库，集成自migrate_onenav.py"""
    results = {"cats_count": 0, "links_count": 0}
    
    # 源数据库连接
    source_conn = sqlite3.connect(db_path)
    source_conn.row_factory = sqlite3.Row
    
    # 如果是替换模式，清空现有数据
    if import_type == "replace":
        current_app.logger.info("执行替换模式，清空现有数据...")
        Website.query.delete()
        Category.query.delete()
        db.session.commit()
    
    # 首先迁移分类
    category_mapping = {}  # 存储旧ID到新ID的映射
    cursor = source_conn.cursor()
    
    # 获取所有分类
    cursor.execute("SELECT * FROM on_categorys ORDER BY weight DESC")
    categories = cursor.fetchall()
    
    # 获取现有分类（合并模式使用）
    existing_categories = {}
    if import_type == "merge":
        existing_categories = {c.name.lower(): c for c in Category.query.all()}
    
    # 先处理一级分类
    for category in categories:
        if category['fid'] == 0:  # 一级分类
            # 检查合并模式下是否已存在同名分类
            cat_name = category['name'].lower()
            if import_type == "merge" and cat_name in existing_categories:
                # 使用现有分类ID
                category_mapping[category['id']] = existing_categories[cat_name].id
            else:
                # 创建新分类
                new_category = Category(
                    name=category['name'],
                    description=category['description'] or '',
                    icon=map_icon(category['font_icon']),
                    order=category['weight']
                )
                db.session.add(new_category)
                db.session.flush()  # 获取新ID
                
                # 保存ID映射关系
                category_mapping[category['id']] = new_category.id
                if import_type == "merge":
                    existing_categories[cat_name] = new_category
    
    # 再处理二级分类
    for category in categories:
        if category['fid'] != 0:  # 二级分类
            # 检查父分类是否已迁移
            if category['fid'] in category_mapping:
                # 检查合并模式下是否已存在同名分类
                cat_name = category['name'].lower()
                if import_type == "merge" and cat_name in existing_categories:
                    # 使用现有分类ID
                    category_mapping[category['id']] = existing_categories[cat_name].id
                else:
                    # 创建新分类
                    new_category = Category(
                        name=category['name'],
                        description=category['description'] or '',
                        icon=map_icon(category['font_icon']),
                        order=category['weight'],
                        parent_id=category_mapping[category['fid']]
                    )
                    db.session.add(new_category)
                    db.session.flush()
                    
                    # 保存ID映射关系
                    category_mapping[category['id']] = new_category.id
                    if import_type == "merge":
                        existing_categories[cat_name] = new_category
    
    db.session.commit()
    results["cats_count"] = len(category_mapping)
    
    # 获取现有URL，避免重复导入
    existing_urls = {}
    if import_type == "merge":
        existing_urls = {w.url.lower(): True for w in Website.query.all()}
    
    # 迁移链接
    cursor.execute("SELECT * FROM on_links ORDER BY fid, weight DESC")
    links = cursor.fetchall()
    
    migrated_count = 0
    skipped_count = 0
    
    for link in links:
        # 检查分类是否已迁移
        if link['fid'] in category_mapping:
            # 检查URL是否重复（合并模式）
            url_lower = link['url'].lower()
            if import_type == "merge" and url_lower in existing_urls:
                skipped_count += 1
                continue
                
            # 转换时间戳为datetime
            try:
                add_time = datetime.fromtimestamp(int(link['add_time']))
            except:
                add_time = datetime.now()
            
            try:
                new_website = Website(
                    title=link['title'],
                    url=link['url'],
                    description=link['description'] or '',
                    icon=link['font_icon'] or '',
                    category_id=category_mapping[link['fid']],
                    created_by_id=admin_id,
                    created_at=add_time,
                    sort_order=link['weight'] or 0,
                    is_private=(link['property'] == 1),  # 假设property=1表示私有
                    views=link['click'] or 0
                )
                db.session.add(new_website)
                migrated_count += 1
                if import_type == "merge":
                    existing_urls[url_lower] = True
                
                # 每100条提交一次，避免内存问题
                if migrated_count % 100 == 0:
                    db.session.commit()
            except Exception as e:
                skipped_count += 1
                current_app.logger.error(f"链接导入错误 {link['title']}: {str(e)}")
        else:
            skipped_count += 1
    
    # 保存所有更改
    db.session.commit()
    results["links_count"] = migrated_count
    
    # 关闭连接
    source_conn.close()
    return results

def map_icon(font_icon):
    """处理OneNav的图标格式"""
    # 如果是URL格式，直接返回
    if font_icon and (font_icon.startswith('http://') or font_icon.startswith('https://')):
        return font_icon
    
    # 如果是Font Awesome图标格式，保留原格式
    if font_icon and ('fa-' in font_icon):
        # 确保格式正确，添加fa前缀如果没有的话
        if not font_icon.startswith('fa ') and not font_icon.startswith('fas '):
            return 'fa ' + font_icon.strip()
        return font_icon
    
    # 如果不是Font Awesome格式但有值，转为Bootstrap格式
    if font_icon:
        return 'bi-' + font_icon.strip()
    
    # 默认图标
    return 'bi-link'

def is_valid_sqlite_db(file_path):
    """检查文件是否为有效的SQLite数据库"""
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        cursor.fetchall()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def is_onenav_db(file_path):
    """检查是否为OneNav格式的数据库"""
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='on_categorys' OR name='on_links'")
        result = cursor.fetchall()
        conn.close()
        return len(result) >= 2  # 至少包含分类和链接表
    except sqlite3.Error:
        return False

def convert_to_onenav_format(db_path):
    """将系统数据库转换为OneNav格式（导出时使用）"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建OneNav表结构
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS on_categorys (
            id INTEGER PRIMARY KEY,
            name TEXT(32),
            add_time TEXT(10),
            up_time TEXT(10),
            weight integer(3),
            property integer(1),
            description TEXT(128),
            font_icon TEXT(32),
            fid INTEGER
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS on_links (
            id INTEGER PRIMARY KEY,
            fid INTEGER(5),
            title TEXT(64),
            url TEXT(256),
            description TEXT(256),
            add_time TEXT(10),
            up_time TEXT(10),
            weight integer(3),
            property integer(1),
            click INTEGER,
            topping INTEGER,
            url_standby TEXT(256),
            font_icon TEXT(512),
            check_status INTEGER,
            last_checked_time TEXT
        )
        ''')
        
        # 转换分类数据 - 修改SQL，为order字段添加引号避免SQL关键字冲突
        cursor.execute('''
        SELECT c.id, c.name, c.description, c.icon, c."order", c.parent_id, c.created_at
        FROM category c
        ''')
        categories = cursor.fetchall()
        
        for cat in categories:
            cat_id, name, desc, icon, order, parent_id, created_at = cat
            # 转换时间戳
            try:
                # 处理created_at为None或字符串的情况
                if created_at is None:
                    add_time = int(datetime.now().timestamp())
                elif isinstance(created_at, str):
                    # 尝试解析字符串格式的时间
                    try:
                        dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        add_time = int(dt.timestamp())
                    except:
                        add_time = int(datetime.now().timestamp())
                else:
                    # 尝试作为datetime对象处理
                    add_time = int(created_at.timestamp())
            except:
                add_time = int(datetime.now().timestamp())
                
            up_time = add_time
            weight = order or 0
            property = 0  # 默认公开
            fid = parent_id or 0  # 父分类ID
            
            # 确保值的类型正确
            name = str(name) if name else ''
            desc = str(desc) if desc else ''
            icon = str(icon) if icon else ''
            
            cursor.execute('''
            INSERT INTO on_categorys (id, name, add_time, up_time, weight, property, description, font_icon, fid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cat_id, name, str(add_time), str(up_time), weight, property, desc, icon, fid))
        
        # 转换链接数据
        cursor.execute('''
        SELECT w.id, w.category_id, w.title, w.url, w.description, w.icon, w.created_at, 
               w.sort_order, w.is_private, w.views
        FROM website w
        ''')
        websites = cursor.fetchall()
        
        for site in websites:
            site_id, category_id, title, url, desc, icon, created_at, sort_order, is_private, views = site
            # 转换时间戳
            try:
                # 处理created_at为None或字符串的情况
                if created_at is None:
                    add_time = int(datetime.now().timestamp())
                elif isinstance(created_at, str):
                    # 尝试解析字符串格式的时间
                    try:
                        dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        add_time = int(dt.timestamp())
                    except:
                        add_time = int(datetime.now().timestamp())
                else:
                    # 尝试作为datetime对象处理
                    add_time = int(created_at.timestamp())
            except:
                add_time = int(datetime.now().timestamp())
                
            up_time = add_time
            weight = sort_order or 0
            property = 1 if is_private else 0
            fid = category_id or 0
            
            # 确保值的类型正确
            title = str(title) if title else ''
            url = str(url) if url else ''
            desc = str(desc) if desc else ''
            icon = str(icon) if icon else ''
            views = int(views) if views else 0
            
            cursor.execute('''
            INSERT INTO on_links (id, fid, title, url, description, add_time, up_time, weight, property, click, 
                                topping, font_icon, check_status, last_checked_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (site_id, fid, title, url, desc, str(add_time), str(up_time), weight, property, 
                views, 0, icon, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        current_app.logger.info(f"成功将数据转换为OneNav格式，导出{len(categories)}个分类和{len(websites)}个链接")
        return True
    except Exception as e:
        current_app.logger.error(f"转换数据库格式失败: {str(e)}")
        return False

# 添加清空链接数据的路由
@bp.route('/clear-websites', methods=['POST'])
@login_required
@superadmin_required
def clear_websites():
    """清空所有网站链接数据"""
    try:
        # 获取当前链接数量
        website_count = Website.query.count()
        
        # 删除所有链接数据
        Website.query.delete()
        
        # 提交更改
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f"已清空所有网站链接数据，共删除{website_count}条记录")
        
        return jsonify({'success': True, 'message': f'已成功删除{website_count}条链接数据'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空链接数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

# 添加清空所有数据的路由
@bp.route('/clear-all-data', methods=['POST'])
@login_required
@superadmin_required
def clear_all_data():
    """清空所有网站和分类数据"""
    try:
        # 获取当前数据量
        website_count = Website.query.count()
        category_count = Category.query.count()
        
        # 先删除所有链接数据（因为有外键约束）
        Website.query.delete()
        
        # 再删除所有分类数据
        Category.query.delete()
        
        # 提交更改
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f"已清空所有数据，共删除{website_count}条链接和{category_count}个分类")
        
        return jsonify({
            'success': True, 
            'message': f'已成功删除{website_count}条链接和{category_count}个分类'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空所有数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

# 添加备份管理功能
@bp.route('/backup-data')
@login_required
@superadmin_required
def backup_data():
    """创建数据库备份"""
    # 确定时间戳和文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"booknav_{timestamp}.db3"
    
    # 确保备份目录存在
    backup_dir = os.path.join(current_app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份文件路径
    backup_path = os.path.join(backup_dir, filename)
    
    try:
        # 复制当前数据库
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        current_app.logger.info(f"准备备份数据库到 {backup_path}")
        
        # 数据库路径可能是相对路径，需要转换为绝对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.root_path, db_path)
            current_app.logger.info(f"转换为绝对路径: {db_path}")
        
        # 检查源文件是否存在
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"找不到数据库文件: {db_path}")
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        current_app.logger.info(f"数据库备份成功: {backup_path}")
        
        flash('数据库备份成功', 'success')
        return redirect(url_for('admin.backup_list'))
    except Exception as e:
        current_app.logger.error(f"数据库备份失败: {str(e)}")
        flash(f'数据库备份失败: {str(e)}', 'danger')
        return redirect(url_for('admin.backup_list'))

@bp.route('/backup-list')
@login_required
@superadmin_required
def backup_list():
    """备份列表管理页面"""
    # 确保备份目录存在
    backup_dir = os.path.join(current_app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # 获取所有备份文件
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.db3'):
            file_path = os.path.join(backup_dir, filename)
            file_stats = os.stat(file_path)
            
            # 提取备份时间
            try:
                # 从文件名中提取时间，格式如 booknav_20250414193523.db3
                time_str = filename.split('_')[1].split('.')[0]
                backup_time = datetime.strptime(time_str, '%Y%m%d%H%M%S')
                time_display = backup_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_display = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            backups.append({
                'filename': filename,
                'size': file_stats.st_size,
                'size_display': format_file_size(file_stats.st_size),
                'time': file_stats.st_mtime,
                'time_display': time_display
            })
    
    # 按时间降序排序
    backups.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('admin/backup_list.html', title='备份管理', backups=backups)

@bp.route('/download-backup/<filename>')
@login_required
@superadmin_required
def download_backup(filename):
    """下载备份文件"""
    # 安全检查，确保文件名不包含路径分隔符
    if os.path.sep in filename or '..' in filename:
        abort(404)
    
    backup_dir = os.path.join(current_app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(backup_path):
        flash('备份文件不存在', 'danger')
        return redirect(url_for('admin.backup_list'))
    
    try:
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"下载备份文件失败: {str(e)}")
        flash(f'下载失败: {str(e)}', 'danger')
        return redirect(url_for('admin.backup_list'))

@bp.route('/delete-backup/<filename>', methods=['POST'])
@login_required
@superadmin_required
def delete_backup(filename):
    """删除备份文件"""
    # 安全检查，确保文件名不包含路径分隔符
    if os.path.sep in filename or '..' in filename:
        abort(404)
    
    backup_dir = os.path.join(current_app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(backup_path):
        flash('备份文件不存在', 'danger')
        return redirect(url_for('admin.backup_list'))
    
    try:
        os.remove(backup_path)
        flash('备份文件已删除', 'success')
    except Exception as e:
        current_app.logger.error(f"删除备份文件失败: {str(e)}")
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup_list'))

@bp.route('/restore-backup/<filename>', methods=['POST'])
@login_required
@superadmin_required
def restore_backup(filename):
    """恢复备份"""
    # 安全检查，确保文件名不包含路径分隔符
    if os.path.sep in filename or '..' in filename:
        abort(404)
    
    backup_dir = os.path.join(current_app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(backup_path):
        flash('备份文件不存在', 'danger')
        return redirect(url_for('admin.backup_list'))
    
    try:
        # 目标数据库路径
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # 数据库路径可能是相对路径，需要转换为绝对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.root_path, db_path)
        
        # 关闭数据库连接
        db.session.close()
        db.engine.dispose()
        
        # 先创建当前数据库的临时备份
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        temp_backup = f"{db_path}.restore_bak.{timestamp}"
        shutil.copy2(db_path, temp_backup)
        
        # 恢复备份
        shutil.copy2(backup_path, db_path)
        
        flash('数据库恢复成功，请重新登录', 'success')
        # 恢复后需要重新登录
        return redirect(url_for('auth.logout'))
    except Exception as e:
        current_app.logger.error(f"恢复备份失败: {str(e)}")
        flash(f'恢复失败: {str(e)}', 'danger')
        return redirect(url_for('admin.backup_list'))

def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"

# 批量抓取缺失图标相关功能
from app.main.routes import get_website_icon
import time
import json
import threading
from queue import Queue

# 用于存储批量处理的状态
icon_fetch_status = {
    'is_running': False,
    'total': 0,
    'processed': 0,
    'success': 0,
    'failed': 0,
    'start_time': None
}

# 创建队列和线程事件，用于控制抓取过程
icon_fetch_queue = Queue()
icon_fetch_stop_event = threading.Event()

@bp.route('/api/batch-fetch-icons', methods=['POST'])
@login_required
@superadmin_required
def batch_fetch_icons():
    """开始批量抓取缺失的图标"""
    global icon_fetch_status
    
    # 检查是否已有正在进行的批量处理
    if icon_fetch_status['is_running']:
        return jsonify({
            'success': False,
            'message': '已有批量抓取任务正在运行，请等待其完成'
        })
    
    # 重置状态
    icon_fetch_status = {
        'is_running': True,
        'total': 0,
        'processed': 0,
        'success': 0,
        'failed': 0,
        'start_time': time.time()
    }
    
    # 清除可能的停止标志
    icon_fetch_stop_event.clear()
    
    # 获取当前应用实例传递给线程
    app = current_app._get_current_object()  # 获取真实的应用对象
    
    # 启动后台线程处理
    threading.Thread(target=process_missing_icons, args=(app,)).start()
    
    return jsonify({
        'success': True,
        'message': '批量抓取图标任务已启动'
    })

@bp.route('/api/batch-fetch-icons/status')
@login_required
@superadmin_required
def batch_fetch_icons_status():
    """获取批量抓取过程的状态"""
    global icon_fetch_status
    
    # 计算执行时间
    elapsed_time = ""
    if icon_fetch_status['start_time']:
        elapsed_seconds = int(time.time() - icon_fetch_status['start_time'])
        minutes, seconds = divmod(elapsed_seconds, 60)
        elapsed_time = f"{minutes}分{seconds}秒"
    
    return jsonify({
        'is_running': icon_fetch_status['is_running'],
        'total': icon_fetch_status['total'],
        'processed': icon_fetch_status['processed'],
        'success': icon_fetch_status['success'],
        'failed': icon_fetch_status['failed'],
        'elapsed_time': elapsed_time,
        'percent': 0 if icon_fetch_status['total'] == 0 else int((icon_fetch_status['processed'] / icon_fetch_status['total']) * 100)
    })

@bp.route('/api/batch-fetch-icons/stop', methods=['POST'])
@login_required
@superadmin_required
def batch_fetch_icons_stop():
    """停止批量抓取图标任务"""
    global icon_fetch_status
    
    if not icon_fetch_status['is_running']:
        return jsonify({
            'success': False,
            'message': '没有正在运行的抓取任务'
        })
    
    # 设置停止标志
    icon_fetch_stop_event.set()
    
    return jsonify({
        'success': True,
        'message': '已发送停止信号，任务将在当前图标处理完成后停止'
    })

def process_missing_icons(app):
    """后台处理所有缺失图标的网站"""
    global icon_fetch_status
    
    # 在线程中使用应用上下文
    with app.app_context():
        try:
            # 查询所有缺失图标的网站
            missing_icon_websites = Website.query.filter(
                (Website.icon.is_(None)) | 
                (Website.icon == '') | 
                (Website.icon.like('%cccyun.cc%'))  # 包含备用图标的网站
            ).all()
            
            # 更新总数
            icon_fetch_status['total'] = len(missing_icon_websites)
            
            # 记录日志
            current_app.logger.info(f"开始批量抓取图标，共{len(missing_icon_websites)}个网站")
            
            # 处理每个网站
            for website in missing_icon_websites:
                # 检查是否收到了停止信号
                if icon_fetch_stop_event.is_set():
                    current_app.logger.info("收到停止信号，中断批量抓取")
                    break
                    
                try:
                    # 抓取图标
                    result = get_website_icon(website.url)
                    
                    # 根据结果更新网站图标
                    if result["success"] and result.get("icon_url"):
                        # 使用API返回的图标URL
                        website.icon = result["icon_url"]
                        icon_fetch_status['success'] += 1
                    elif "fallback_url" in result and result["fallback_url"]:
                        # 验证备用图标URL是否可访问
                        fallback_url = result["fallback_url"]
                        try:
                            # 使用HEAD请求快速验证URL可访问性
                            head_response = requests.head(
                                fallback_url, 
                                timeout=5, 
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )
                            if head_response.status_code < 400:  # 2xx或3xx状态码表示可访问
                                # 备用URL可访问，设置图标并算作成功
                                website.icon = fallback_url
                                icon_fetch_status['success'] += 1
                            else:
                                # 备用URL返回错误状态码，算作失败
                                icon_fetch_status['failed'] += 1
                        except Exception as url_err:
                            # 请求过程中出错，算作失败
                            current_app.logger.warning(f"验证备用图标URL失败: {fallback_url} - {str(url_err)}")
                            icon_fetch_status['failed'] += 1
                    else:
                        # 完全无法获取图标才算失败
                        icon_fetch_status['failed'] += 1
                    
                    # 更新处理数量
                    icon_fetch_status['processed'] += 1
                    
                    # 每10个网站提交一次，避免长事务
                    if icon_fetch_status['processed'] % 10 == 0:
                        db.session.commit()
                        
                    # 适当休眠，避免API限制
                    time.sleep(1)
                    
                except Exception as e:
                    # 处理异常，尝试使用备用图标
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(website.url)
                        domain = parsed_url.netloc
                        fallback_url = f"https://favicon.cccyun.cc/{domain}"
                        
                        # 验证备用图标URL是否可访问
                        try:
                            # 使用HEAD请求快速验证URL可访问性
                            head_response = requests.head(
                                fallback_url, 
                                timeout=5, 
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )
                            if head_response.status_code < 400:  # 2xx或3xx状态码表示可访问
                                # 备用URL可访问，设置图标并算作成功
                                website.icon = fallback_url
                                icon_fetch_status['success'] += 1
                            else:
                                # 备用URL返回错误状态码，算作失败
                                icon_fetch_status['failed'] += 1
                        except Exception as url_err:
                            # 请求过程中出错，算作失败
                            current_app.logger.warning(f"验证备用图标URL失败: {fallback_url} - {str(url_err)}")
                            icon_fetch_status['failed'] += 1
                    except:
                        # 完全无法设置图标才算失败
                        icon_fetch_status['failed'] += 1
                    
                    icon_fetch_status['processed'] += 1
                    current_app.logger.error(f"抓取图标出错 ({website.url}): {str(e)}")
            
            # 提交所有更改
            db.session.commit()
            current_app.logger.info(f"批量抓取图标完成，成功: {icon_fetch_status['success']}，失败: {icon_fetch_status['failed']}")
            
        except Exception as e:
            current_app.logger.error(f"批量抓取图标任务出错: {str(e)}")
        finally:
            # 更新状态为已完成
            icon_fetch_status['is_running'] = False

def is_project_db(db_path):
    """检查是否为本项目数据库格式"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否包含项目特有的表结构
        required_tables = ['category', 'website', 'user']
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                conn.close()
                return False
        
        # 检查category表是否有color字段（本项目特有）
        cursor.execute("PRAGMA table_info(category)")
        columns = cursor.fetchall()
        has_color = False
        for column in columns:
            if column[1] == 'color':
                has_color = True
                break
        
        conn.close()
        return has_color
    except Exception as e:
        current_app.logger.error(f"检查项目数据库格式失败: {str(e)}")
        return False

def import_project_db(db_path, import_type, admin_id):
    """导入本项目格式的数据库"""
    try:
        # 备份现有数据库
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"pre_import_backup_{timestamp}.db3"
        backup_dir = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制当前数据库作为备份
        db_path_current = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.isabs(db_path_current):
            db_path_current = os.path.join(current_app.root_path, db_path_current)
        shutil.copy2(db_path_current, backup_path)
        
        # 如果是替换模式，直接使用导入的数据库替换现有数据库
        if import_type == "replace":
            current_app.logger.info("执行替换模式，直接替换数据库文件")
            shutil.copy2(db_path, db_path_current)
            
            # 重新连接数据库（强制SQLAlchemy重新加载数据）
            db.session.remove()
            db.engine.dispose()
            
            # 获取数据库统计信息
            conn = sqlite3.connect(db_path_current)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM category")
            cat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM website")
            link_count = cursor.fetchone()[0]
            conn.close()
            
            return True, cat_count, link_count
        else:
            # 合并模式：保留现有数据，添加新数据
            current_app.logger.info("执行合并模式，从导入的数据库添加数据")
            
            # 连接源数据库
            source_conn = sqlite3.connect(db_path)
            source_cursor = source_conn.cursor()
            
            # 获取分类数据
            source_cursor.execute("SELECT id, name, description, icon, color, \"order\", parent_id FROM category")
            categories = source_cursor.fetchall()
            
            # 获取网站数据
            source_cursor.execute("""
                SELECT id, title, url, description, icon, views, is_featured, sort_order, 
                       category_id, is_private 
                FROM website
            """)
            websites = source_cursor.fetchall()
            
            # 关闭源数据库连接
            source_conn.close()
            
            # 导入分类
            cat_id_mapping = {}  # 旧ID到新ID的映射
            existing_categories = {c.name.lower(): c for c in Category.query.all()}
            
            for cat in categories:
                cat_id, name, desc, icon, color, order, parent_id = cat
                
                # 检查是否已存在同名分类
                cat_name = name.lower() if name else ""
                if cat_name in existing_categories:
                    # 使用现有分类ID
                    cat_id_mapping[cat_id] = existing_categories[cat_name].id
                else:
                    # 创建新分类
                    new_category = Category(
                        name=name,
                        description=desc or "",
                        icon=icon or "folder",
                        color=color or "#3498db",
                        order=order or 0
                    )
                    db.session.add(new_category)
                    db.session.flush()  # 获取新ID
                    
                    # 保存ID映射关系
                    cat_id_mapping[cat_id] = new_category.id
                    existing_categories[cat_name] = new_category
            
            db.session.commit()
            
            # 更新父子关系
            for cat in categories:
                cat_id, _, _, _, _, _, parent_id = cat
                if parent_id and parent_id in cat_id_mapping and cat_id in cat_id_mapping:
                    child = Category.query.get(cat_id_mapping[cat_id])
                    if child:
                        child.parent_id = cat_id_mapping[parent_id]
            
            db.session.commit()
            
            # 导入网站数据
            existing_urls = {w.url.lower(): True for w in Website.query.all()}
            imported_count = 0
            
            for site in websites:
                site_id, title, url, desc, icon, views, is_featured, sort_order, category_id, is_private = site
                
                # 检查URL是否已存在
                url_lower = url.lower() if url else ""
                if url_lower and url_lower in existing_urls:
                    continue
                
                # 确定新的分类ID
                new_cat_id = None
                if category_id and category_id in cat_id_mapping:
                    new_cat_id = cat_id_mapping[category_id]
                
                # 创建新网站
                new_website = Website(
                    title=title,
                    url=url,
                    description=desc or "",
                    icon=icon,
                    views=views or 0,
                    is_featured=bool(is_featured),
                    sort_order=sort_order or 0,
                    category_id=new_cat_id,
                    created_by_id=admin_id,
                    is_private=bool(is_private),
                    created_at=datetime.now()
                )
                db.session.add(new_website)
                imported_count += 1
                
                # 每100条提交一次，避免内存问题
                if imported_count % 100 == 0:
                    db.session.commit()
            
            db.session.commit()
            return True, len(cat_id_mapping), imported_count
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"导入本项目数据库失败: {str(e)}")
        raise e

@bp.route('/wallpaper', methods=['GET', 'POST'])
@login_required
@admin_required
def wallpaper():
    """背景管理页面"""
    form = BackgroundForm()
    
    if form.validate_on_submit():
        background = Background(
            title=form.title.data,
            type=form.type.data,
            device_type=form.device_type.data,
            created_by_id=current_user.id
        )
        
        # 处理图片上传
        if form.background_file.data and form.type.data == 'image':
            bg_filename = save_image(form.background_file.data, 'backgrounds')
            if bg_filename:
                background.url = url_for('static', filename=f'uploads/backgrounds/{bg_filename}')
        elif form.url.data:
            background.url = form.url.data
        
        db.session.add(background)
        db.session.commit()
        flash('背景添加成功', 'success')
        return redirect(url_for('admin.wallpaper'))
    
    backgrounds = Background.query.order_by(Background.created_at.desc()).all()
    return render_template('admin/wallpaper.html', title='背景管理', form=form, backgrounds=backgrounds)


@bp.route('/apply-background', methods=['POST'])
@login_required
@admin_required
def apply_background():
    """应用背景"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    bg_id = data.get('id')
    bg_type = data.get('type')
    bg_url = data.get('url')
    
    if not all([bg_type, bg_url]):
        return jsonify({'success': False, 'message': '缺少必要参数'})
    
    try:
        settings = SiteSettings.get_settings()
        settings.background_type = bg_type
        settings.background_url = bg_url
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/delete-background/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_background(id):
    """删除背景"""
    background = Background.query.get_or_404(id)
    
    # 检查权限（只有超级管理员或创建者可以删除）
    if not current_user.is_superadmin and background.created_by_id != current_user.id:
        return jsonify({'success': False, 'message': '没有权限删除此背景'})
    
    try:
        # 保存图片URL用于后续删除文件
        bg_url = background.url
        
        # 如果当前正在使用这个背景，则重置默认背景
        settings = SiteSettings.get_settings()
        if settings.background_url == background.url:
            settings.background_type = 'none'
            settings.background_url = None
        
        # 从数据库中删除记录
        db.session.delete(background)
        db.session.commit()
        
        # 删除物理文件（仅针对上传的图片，不删除外部URL）
        if bg_url and '/static/uploads/backgrounds/' in bg_url:
            try:
                # 从URL中提取文件名
                file_path = bg_url.split('/static/')[1]
                full_path = os.path.join(current_app.root_path, 'static', file_path)
                
                # 检查文件是否存在，如果存在则删除
                if os.path.exists(full_path):
                    os.remove(full_path)
                    current_app.logger.info(f'已删除背景图片文件: {full_path}')
            except Exception as e:
                current_app.logger.error(f'删除背景图片文件失败: {str(e)}')
                # 文件删除失败不影响整体操作，继续返回成功
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/clear-background', methods=['POST'])
@login_required
@admin_required
def clear_background():
    """清除背景，恢复默认背景"""
    try:
        settings = SiteSettings.get_settings()
        settings.background_type = 'none'
        settings.background_url = None
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
