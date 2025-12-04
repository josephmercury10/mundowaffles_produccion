"""alter printers tipo and perfil to Text for multi-values

Revision ID: 20251203_alter_printers
Revises: 20251202_add_printers
Create Date: 2025-12-03 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251203_alter_printers'
down_revision = '20251202_add_printers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alterar columnas tipo y perfil de VARCHAR a TEXT para soportar JSON arrays
    op.alter_column('printers', 'tipo',
                    existing_type=sa.String(length=30),
                    type_=sa.Text(),
                    existing_nullable=False)
    op.alter_column('printers', 'perfil',
                    existing_type=sa.String(length=30),
                    type_=sa.Text(),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column('printers', 'tipo',
                    existing_type=sa.Text(),
                    type_=sa.String(length=30),
                    existing_nullable=False)
    op.alter_column('printers', 'perfil',
                    existing_type=sa.Text(),
                    type_=sa.String(length=30),
                    existing_nullable=False)
