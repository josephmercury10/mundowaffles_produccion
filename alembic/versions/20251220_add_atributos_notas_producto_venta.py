"""add atributos_seleccionados and notas to producto_venta

Revision ID: 20251220_add_atributos_notas
Revises: 20251208_add_metodos_pago
Create Date: 2025-12-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251220_add_atributos_notas'
down_revision = '20251208_add_metodos_pago'
branch_labels = None
depends_on = None


def upgrade():
    """Agregar campo notas (Text) a producto_venta"""
    
    # Agregar campo notas (Text)
    # Permite registrar comentarios especiales para cada producto en el pedido
    op.add_column('producto_venta', 
                  sa.Column('notas', sa.Text(), nullable=True))


def downgrade():
    """Revertir cambios: eliminar campos agregados"""
    
    op.drop_column('producto_venta', 'notas')
