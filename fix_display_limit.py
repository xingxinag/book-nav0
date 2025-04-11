"""
修复Category表中的display_limit字段，确保没有NULL值
"""
import os
import sqlite3
from app import create_app, db
from app.models import Category

# 创建应用上下文
app = create_app()
app.app_context().push()

print("检查Category表中display_limit为NULL的记录...")
null_categories = Category.query.filter(Category.display_limit == None).all()

if null_categories:
    print(f"发现{len(null_categories)}个分类的display_limit为NULL，正在修复...")
    for category in null_categories:
        print(f"修复分类: {category.name}, 设置display_limit=8")
        category.display_limit = 8
    
    db.session.commit()
    print("修复完成！")
else:
    print("没有发现NULL值，所有分类的display_limit字段都有值。")

# 打印所有分类的display_limit值以验证
print("\n当前所有分类的display_limit值:")
all_categories = Category.query.all()
for category in all_categories:
    print(f"分类: {category.name}, display_limit: {category.display_limit}") 