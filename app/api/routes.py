from flask import jsonify, request
from flask_login import current_user, login_required
from app import db
from app.api import bp
from app.models import Website

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