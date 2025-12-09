"""add metodos_pago table and payment fields to ventas

Revision ID: 20251208_add_metodos_pago
Revises: 20251203_alter_printers_multi_profiles
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251208_add_metodos_pago'
down_revision = '20251205_update_printer_tipos'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla metodos_pago (catálogo)
    op.create_table(
        'metodos_pago',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(50), nullable=False),
        sa.Column('requiere_monto_recibido', sa.Boolean(), default=False),
        sa.Column('requiere_referencia', sa.Boolean(), default=False),
        sa.Column('estado', sa.SmallInteger(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Agregar campos de pago a la tabla ventas
    op.add_column('ventas', sa.Column('metodo_pago_id', sa.BigInteger(), nullable=True))
    op.add_column('ventas', sa.Column('monto_recibido', sa.Numeric(12, 2), nullable=True))
    op.add_column('ventas', sa.Column('vuelto', sa.Numeric(12, 2), nullable=True))
    op.add_column('ventas', sa.Column('referencia_pago', sa.String(100), nullable=True))
    op.add_column('ventas', sa.Column('fecha_pago', sa.DateTime(), nullable=True))
    
    # Crear FK
    op.create_foreign_key(
        'fk_ventas_metodo_pago',
        'ventas', 'metodos_pago',
        ['metodo_pago_id'], ['id']
    )
    
    # Insertar datos iniciales en metodos_pago
    op.execute("""
        INSERT INTO metodos_pago (nombre, requiere_monto_recibido, requiere_referencia, estado, created_at)
        VALUES 
            ('Efectivo', TRUE, FALSE, 1, NOW()),
            ('Tarjeta Débito', FALSE, TRUE, 1, NOW()),
            ('Tarjeta Crédito', FALSE, TRUE, 1, NOW()),
            ('Transferencia', FALSE, TRUE, 1, NOW())
    """)


def downgrade():
    # Eliminar FK
    op.drop_constraint('fk_ventas_metodo_pago', 'ventas', type_='foreignkey')
    
    # Eliminar campos de ventas
    op.drop_column('ventas', 'fecha_pago')
    op.drop_column('ventas', 'referencia_pago')
    op.drop_column('ventas', 'vuelto')
    op.drop_column('ventas', 'monto_recibido')
    op.drop_column('ventas', 'metodo_pago_id')
    
    # Eliminar tabla metodos_pago
    op.drop_table('metodos_pago')
