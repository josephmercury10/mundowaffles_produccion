from utils.db import db
from datetime import datetime


class MetodoPago(db.Model):
    """Catálogo de métodos de pago disponibles"""
    __tablename__ = 'metodos_pago'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)  # Efectivo, Tarjeta Débito, etc.
    requiere_monto_recibido = db.Column(db.Boolean, default=False)  # True para efectivo
    requiere_referencia = db.Column(db.Boolean, default=False)  # True para transferencia/tarjeta
    estado = db.Column(db.SmallInteger, nullable=False, default=1)  # 1=activo, 0=inactivo
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación con ventas
    ventas = db.relationship('Venta', backref='metodo_pago', lazy=True)
    
    def __repr__(self):
        return f'<MetodoPago {self.nombre}>'
