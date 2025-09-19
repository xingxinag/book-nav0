"""添加WebDAV备份相关字段

Revision ID: webdav20250919
Revises: ann20240423
Create Date: 2025-09-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'webdav20250919'
down_revision = 'ann20240423'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.add_column(sa.Column('webdav_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('webdav_url', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('webdav_username', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('webdav_password', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('webdav_path', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('webdav_auto_backup', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('webdav_keep_local', sa.Boolean(), nullable=True))

def downgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.drop_column('webdav_enabled')
        batch_op.drop_column('webdav_url')
        batch_op.drop_column('webdav_username')
        batch_op.drop_column('webdav_password')
        batch_op.drop_column('webdav_path')
        batch_op.drop_column('webdav_auto_backup')
        batch_op.drop_column('webdav_keep_local')