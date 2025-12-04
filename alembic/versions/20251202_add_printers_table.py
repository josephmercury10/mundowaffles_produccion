"""add printers table

Revision ID: 20251202_add_printers
Revises: 
Create Date: 2025-12-02 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251202_add_printers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'printers',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('driver_name', sa.String(length=150), nullable=False),
        sa.Column('tipo', sa.Text(), nullable=False),  # JSON array
        sa.Column('perfil', sa.Text(), nullable=False),  # JSON array
        sa.Column('ancho_caracteres', sa.SmallInteger(), nullable=False, server_default='42'),
        sa.Column('cortar_papel', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('feed_lines', sa.SmallInteger(), nullable=False, server_default='3'),
        sa.Column('estado', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('printers')
