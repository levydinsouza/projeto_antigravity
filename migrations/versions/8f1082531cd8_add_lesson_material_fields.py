"""Add lesson material fields

Revision ID: 8f1082531cd8
Revises: fb5bef3b55ee
Create Date: 2026-06-30 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f1082531cd8'
down_revision = 'fb5bef3b55ee'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pdf_url', sa.String(length=500), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('pdf_public_id', sa.String(length=300), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('html_url', sa.String(length=500), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('html_public_id', sa.String(length=300), nullable=True, server_default=''))


def downgrade():
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.drop_column('html_public_id')
        batch_op.drop_column('html_url')
        batch_op.drop_column('pdf_public_id')
        batch_op.drop_column('pdf_url')
