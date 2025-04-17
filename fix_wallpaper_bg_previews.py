#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复背景预览样式问题脚本

解决壁纸管理页面中的CSS内联样式产生的linter错误，
将模板中的内联样式修改为通过JavaScript来设置样式。
"""

import os
import re
import logging
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 模板文件路径
TEMPLATE_PATH = 'app/templates/admin/wallpaper.html'

def backup_template(template_path):
    """创建模板文件备份"""
    from shutil import copyfile
    import datetime
    
    backup_path = f"{template_path}.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        copyfile(template_path, backup_path)
        logger.info(f"已创建模板备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

def fix_template_style():
    """修复模板中的样式问题"""
    if not os.path.exists(TEMPLATE_PATH):
        logger.error(f"模板文件 {TEMPLATE_PATH} 不存在！")
        return False
    
    # 创建备份
    if not backup_template(TEMPLATE_PATH):
        if input("备份创建失败，是否继续? (y/n): ").lower() != 'y':
            return False
    
    try:
        # 读取原始模板内容
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复内容
        modified_content = content
        changes_made = 0
        
        # 1. 修复背景卡片预览的内联样式
        pattern1 = r'style="{% if bg\.type == \'image\' %}background-image: url\(\'{{ bg\.url }}\'\);{% elif bg\.type == \'gradient\' %}background-image: {{ bg\.url }};{% elif bg\.type == \'color\' %}background-color: {{ bg\.url }};{% endif %}"'
        replacement1 = 'data-bg-type="{{ bg.type }}" data-bg-url="{{ bg.url }}"'
        
        # 应用正则替换
        new_content = re.sub(pattern1, replacement1, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes_made += 1
            logger.info("成功替换背景卡片预览的内联样式")
        
        # 2. 修复渐变色预设的内联样式
        pattern2 = r'style="\s*background-image: (linear-gradient\([^;]+\));\s*"(\s*data-gradient="[^"]+")'
        replacement2 = r'data-gradient-style="\1"\2'
        
        new_content = re.sub(pattern2, replacement2, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes_made += 1
            logger.info("成功替换渐变色预设的内联样式")
        
        # 3. 修复纯色预设的内联样式
        pattern3 = r'style="\s*background-color: (#[a-fA-F0-9]{3,6}|rgba?\([^)]+\))\s*"(\s*data-color="[^"]+")'
        replacement3 = r'data-color-style="\1"\2'
        
        new_content = re.sub(pattern3, replacement3, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes_made += 1
            logger.info("成功替换纯色预设的内联样式")
        
        # 4. 修复模态框背景预览的内联样式
        pattern4 = r'style="\s*height: 150px;\s*background-color: #f8f9fa;\s*display: flex;\s*align-items: center;\s*justify-content: center;\s*"'
        replacement4 = 'class="modal-preview-container"'
        
        new_content = re.sub(pattern4, replacement4, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes_made += 1
            logger.info("成功替换模态框背景预览的内联样式")
        
        if changes_made == 0:
            logger.warning("未找到需要替换的内联样式模式")
            return False
            
        # 添加JavaScript代码来设置样式
        js_code = """
  // 设置背景预览样式
  document.addEventListener("DOMContentLoaded", function() {
    // 设置背景卡片预览样式
    document.querySelectorAll('.bg-card-preview').forEach(preview => {
      const bgType = preview.getAttribute('data-bg-type');
      const bgUrl = preview.getAttribute('data-bg-url');
      
      if (bgType && bgUrl) {
        if (bgType === 'image') {
          preview.style.backgroundImage = `url('${bgUrl}')`;
        } else if (bgType === 'gradient') {
          preview.style.backgroundImage = bgUrl;
        } else if (bgType === 'color') {
          preview.style.backgroundColor = bgUrl;
        }
      }
    });
    
    // 设置渐变色预设样式
    document.querySelectorAll('[data-gradient-style]').forEach(item => {
      const gradient = item.getAttribute('data-gradient-style');
      if (gradient) {
        item.style.backgroundImage = gradient;
      }
    });
    
    // 设置纯色预设样式
    document.querySelectorAll('[data-color-style]').forEach(item => {
      const color = item.getAttribute('data-color-style');
      if (color) {
        item.style.backgroundColor = color;
      }
    });
  });"""
        
        # 添加CSS样式
        css_code = """
  .modal-preview-container {
    height: 150px;
    background-color: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: center;
  }"""
        
        # 在现有脚本开始前添加新的脚本
        script_start = "<script>"
        script_insert_point = modified_content.find(script_start)
        
        if script_insert_point != -1:
            modified_content = modified_content[:script_insert_point + len(script_start)] + js_code + modified_content[script_insert_point + len(script_start):]
            logger.info("成功添加JavaScript代码来设置背景样式")
        else:
            logger.warning("未找到合适的位置插入JavaScript代码")
        
        # 在现有样式开始前添加新的样式
        style_start = "<style>"
        style_insert_point = modified_content.find(style_start)
        
        if style_insert_point != -1:
            modified_content = modified_content[:style_insert_point + len(style_start)] + css_code + modified_content[style_insert_point + len(style_start):]
            logger.info("成功添加CSS样式")
        else:
            logger.warning("未找到合适的位置插入CSS样式")
        
        # 写入修改后的内容
        with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logger.info(f"模板文件 {TEMPLATE_PATH} 已成功更新，共进行了 {changes_made} 处修改")
        return True
    
    except Exception as e:
        logger.error(f"修复模板时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始修复壁纸管理页面的样式问题...")
    
    success = fix_template_style()
    
    if success:
        logger.info("修复完成！")
    else:
        logger.error("修复失败，请查看错误日志")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1) 