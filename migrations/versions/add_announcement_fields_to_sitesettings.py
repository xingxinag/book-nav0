"""添加弹窗公告相关字段

Revision ID: ann20240423
Revises: 15f5c88b9d34
Create Date: 2024-04-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ann20240423'
down_revision = '20250423104732'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.add_column(sa.Column('announcement_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('announcement_title', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('announcement_content', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('announcement_link', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('announcement_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('announcement_end', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.drop_column('announcement_enabled')
        batch_op.drop_column('announcement_title')
        batch_op.drop_column('announcement_content')
        batch_op.drop_column('announcement_link')
        batch_op.drop_column('announcement_start')
        batch_op.drop_column('announcement_end') 