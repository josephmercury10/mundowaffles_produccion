"""add_notas_to_producto_venta

Revision ID: bd2d541d405f
Revises: 20251208_add_metodos_pago
Create Date: 2025-12-19 04:25:27.608514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bd2d541d405f'
down_revision: Union[str, Sequence[str], None] = '20251208_add_metodos_pago'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # El campo 'notas' ya existe en la BD (agregado en otra rama)
    # Esta migración solo documenta ese cambio sin ejecutar SQL
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Si necesitas revertir en el futuro, elimina el campo notas
    # op.drop_column('producto_venta', 'notas')
    pass