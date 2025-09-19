"""添加公告不再提示天数设置

Revision ID: ann_remember_days
Revises: ann20240423
Create Date: 2024-04-23 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ann_remember_days'
down_revision = 'ann20240423'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.add_column(sa.Column('announcement_remember_days', sa.Integer(), nullable=True, server_default='7'))

def downgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.drop_column('announcement_remember_days') 