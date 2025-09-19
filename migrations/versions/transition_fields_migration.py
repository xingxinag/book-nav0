"""添加过渡页相关字段

Revision ID: 15f5c88b9d34
Revises: fb0c6f76da1a
Create Date: 2025-04-19 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15f5c88b9d34'
down_revision = 'fb0c6f76da1a'
branch_labels = None
depends_on = None


def upgrade():
    # 添加过渡页相关字段
    op.add_column('site_settings', sa.Column('enable_transition', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('site_settings', sa.Column('transition_time', sa.Integer(), nullable=True, server_default='5'))
    op.add_column('site_settings', sa.Column('admin_transition_time', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('site_settings', sa.Column('transition_ad1', sa.Text(), nullable=True))
    op.add_column('site_settings', sa.Column('transition_ad2', sa.Text(), nullable=True))
    op.add_column('site_settings', sa.Column('transition_remember_choice', sa.Boolean(), nullable=True, server_default='1'))
    op.add_column('site_settings', sa.Column('transition_show_description', sa.Boolean(), nullable=True, server_default='1'))
    op.add_column('site_settings', sa.Column('transition_theme', sa.String(length=32), nullable=True, server_default='default'))
    op.add_column('site_settings', sa.Column('transition_color', sa.String(length=32), nullable=True, server_default='#6e8efb'))


def downgrade():
    # 删除过渡页相关字段
    op.drop_column('site_settings', 'transition_color')
    op.drop_column('site_settings', 'transition_theme')
    op.drop_column('site_settings', 'transition_show_description')
    op.drop_column('site_settings', 'transition_remember_choice')
    op.drop_column('site_settings', 'transition_ad2')
    op.drop_column('site_settings', 'transition_ad1')
    op.drop_column('site_settings', 'admin_transition_time')
    op.drop_column('site_settings', 'transition_time')
    op.drop_column('site_settings', 'enable_transition') 