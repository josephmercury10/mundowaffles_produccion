"""Update printer tipos to match code expectations

Revision ID: 20251205_update_printer_tipos
Revises: 20251204_add_printhost_url_to_printers
Create Date: 2025-12-05 00:00:00

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '20251205_update_printer_tipos'
down_revision = '20251204_add_printhost_url_to_printers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Actualizar tipos de impresoras para que coincidan con las búsquedas del código"""
    connection = op.get_bind()
    
    # Obtener todas las impresoras
    result = connection.execute(sa.text("SELECT id, tipo FROM printers WHERE estado = 1"))
    
    for row in result:
        printer_id, current_tipo = row
        
        # Convertir tipos para que coincidan con el código
        # El código busca: 'comanda', 'venta', 'recibo'
        new_tipo = json.dumps(['comanda', 'venta', 'recibo'])
        
        # Actualizar
        connection.execute(
            sa.text("UPDATE printers SET tipo = :tipo WHERE id = :id"),
            {"tipo": new_tipo, "id": printer_id}
        )
    
    connection.commit()


def downgrade() -> None:
    """Revertir a los tipos anteriores"""
    connection = op.get_bind()
    
    # Revertir a los tipos originales (para referencia)
    old_tipo = json.dumps(['ticket', 'comanda', 'factura', 'cocina'])
    
    connection.execute(
        sa.text("UPDATE printers SET tipo = :tipo WHERE estado = 1"),
        {"tipo": old_tipo}
    )
    
    connection.commit()
