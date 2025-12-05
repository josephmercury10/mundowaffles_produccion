"""add printhost_url to printers

Revision ID: 20251204_add_printhost_url_to_printers
Revises: 20251203_alter_printers_multi_profiles
Create Date: 2025-12-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251204_add_printhost_url_to_printers'
down_revision = '20251203_alter_printers'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('printers', sa.Column('printhost_url', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('printers', 'printhost_url')
