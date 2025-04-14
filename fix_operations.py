"""
添加操作日志模型和后端功能的脚本
"""

MODEL_CODE = """
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
"""

ROUTES_CODE = """
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
"""

USER_DETAIL_ROUTE = """
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
"""

import os
import re

# 修改models.py文件，添加OperationLog模型
def add_operation_log_model():
    models_path = 'app/models.py'
    
    with open(models_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 检查OperationLog模型是否已存在
    if 'class OperationLog' in content:
        print("OperationLog模型已存在，无需添加")
        return
    
    # 在文件末尾添加OperationLog模型
    with open(models_path, 'a', encoding='utf-8') as file:
        file.write('\n\n' + MODEL_CODE)
    
    print("已成功添加OperationLog模型到models.py")

# 修改admin/routes.py，添加操作日志相关API
def add_operation_log_routes():
    routes_path = 'app/admin/routes.py'
    
    with open(routes_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 检查操作日志API是否已存在
    if 'delete_operation_log' in content:
        print("操作日志API已存在，无需添加")
        return
    
    # 确保导入了所需模块
    if 'from app.models import OperationLog' not in content:
        import_line = 'from app.models import User, Category, Website, Tag, InvitationCode, SiteSettings'
        new_import_line = 'from app.models import User, Category, Website, Tag, InvitationCode, SiteSettings, OperationLog'
        content = content.replace(import_line, new_import_line)
    
    # 在文件末尾添加操作日志API
    with open(routes_path, 'a', encoding='utf-8') as file:
        file.write('\n\n' + ROUTES_CODE)
    
    print("已成功添加操作日志API到admin/routes.py")

# 修改用户详情路由，添加操作记录查询
def modify_user_detail_route():
    routes_path = 'app/admin/routes.py'
    
    with open(routes_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 查找user_detail函数
    user_detail_pattern = r'@bp\.route\(\'/user/detail/.*?\'\).*?def user_detail\(.*?\):.*?return render_template\(.*?\)'
    user_detail_match = re.search(user_detail_pattern, content, re.DOTALL)
    
    if not user_detail_match:
        print("找不到user_detail函数，无法修改")
        return
    
    # 替换user_detail函数
    new_content = content.replace(user_detail_match.group(0), USER_DETAIL_ROUTE)
    
    with open(routes_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("已成功修改user_detail路由，添加操作记录查询")

if __name__ == "__main__":
    add_operation_log_model()
    add_operation_log_routes()
    modify_user_detail_route()
    print("操作日志功能添加完成！") 