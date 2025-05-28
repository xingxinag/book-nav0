"""添加设备特定的背景字段

Revision ID: 20250423104732
Revises: 15f5c88b9d34
Create Date: 2024-04-19 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250423104732'
down_revision = '15f5c88b9d34'
branch_labels = None
depends_on = None


def upgrade():
    # 添加PC端背景字段
    op.add_column('site_settings', sa.Column('pc_background_type', sa.String(length=32), nullable=True, server_default='none'))
    op.add_column('site_settings', sa.Column('pc_background_url', sa.String(length=512), nullable=True))
    
    # 添加移动端背景字段
    op.add_column('site_settings', sa.Column('mobile_background_type', sa.String(length=32), nullable=True, server_default='none'))
    op.add_column('site_settings', sa.Column('mobile_background_url', sa.String(length=512), nullable=True))
    
    # 将现有背景设置复制到PC端
    op.execute("""
        UPDATE site_settings 
        SET pc_background_type = background_type,
            pc_background_url = background_url
        WHERE background_type IS NOT NULL OR background_url IS NOT NULL
    """)


def downgrade():
    # 删除新增的字段
    op.drop_column('site_settings', 'pc_background_type')
    op.drop_column('site_settings', 'pc_background_url')
    op.drop_column('site_settings', 'mobile_background_type')
    op.drop_column('site_settings', 'mobile_background_url') 