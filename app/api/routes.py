from flask import jsonify, request
from flask_login import current_user, login_required
from app import db, csrf
from app.api import bp
from app.models import Website, Category

@bp.route('/website/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_website(id):
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '您没有权限执行此操作'
        }), 403

    website = Website.query.get_or_404(id)
    
    try:
        db.session.delete(website)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '网站删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '删除失败：' + str(e)
        }), 500

@bp.route('/website/update/<int:id>', methods=['POST'])
@login_required
def update_website(id):
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '您没有权限执行此操作'
        }), 403

    website = Website.query.get_or_404(id)
    data = request.get_json()

    try:
        website.title = data.get('title', website.title)
        website.url = data.get('url', website.url)
        website.description = data.get('description', website.description)
        website.icon = data.get('icon', website.icon)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '网站信息更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '更新失败：' + str(e)
        }), 500

@bp.route('/category/update_order', methods=['POST'])
@login_required
@csrf.exempt
def update_category_order():
    """更新分类排序顺序的API接口"""
    # 检查当前用户是否为管理员
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    items = data['items']
    print(f"收到分类排序请求: {items}") # 记录排序数据
    
    try:
        # 更新每个分类的排序顺序
        updated_count = 0
        for item in items:
            category_id = item.get('id')
            order = item.get('order')
            
            if category_id is not None and order is not None:
                category = Category.query.get(category_id)
                if category:
                    old_order = category.order
                    category.order = order
                    updated_count += 1
                    print(f"更新分类ID {category_id} 排序: {old_order} -> {order}")
        
        # 保存更改
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'分类排序已更新 ({updated_count} 个分类)'
        })
    except Exception as e:
        db.session.rollback()
        print(f"分类排序更新失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新排序失败: {str(e)}'}), 500 