#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新数据库脚本

检查并确保SiteSettings表中有background_type和background_url字段
"""

import os
import sys
import logging
from app import create_app, db
from app.models import SiteSettings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def update_db():
    """更新数据库结构"""
    app = create_app()
    
    with app.app_context():
        logger.info("检查SiteSettings表...")
        
        # 尝试获取现有设置
        try:
            settings = SiteSettings.query.first()
            if not settings:
                logger.info("创建新的SiteSettings记录...")
                settings = SiteSettings()
                db.session.add(settings)
                
            # 确保background_type字段存在且有值
            # 如果这不抛出异常，说明字段存在
            if hasattr(settings, 'background_type'):
                logger.info(f"background_type字段存在，当前值: {settings.background_type}")
            else:
                logger.warning("background_type字段不存在，这不应该发生")
                
            # 确保background_url字段存在
            if hasattr(settings, 'background_url'):
                logger.info(f"background_url字段存在，当前值: {settings.background_url}")
            else:
                logger.warning("background_url字段不存在，这不应该发生")
                
            # 检查旧字段是否有值，迁移到新字段
            if hasattr(settings, 'background_image') and settings.background_image and not settings.background_url:
                logger.info("将旧背景图片字段值迁移到新字段...")
                settings.background_url = settings.background_image
                settings.background_type = 'image'
            
            # 确保background_type有值
            if not settings.background_type:
                settings.background_type = 'none'
                
            db.session.commit()
            logger.info("数据库更新完成")
            
        except Exception as e:
            logger.error(f"更新数据库时出错: {str(e)}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    logger.info("开始更新数据库...")
    success = update_db()
    sys.exit(0 if success else 1) 