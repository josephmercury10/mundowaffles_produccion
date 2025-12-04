from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal
import json

db = SQLAlchemy()

class Compra(db.Model):
    __tablename__ = 'compras'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    impuesto = db.Column(db.Numeric(8, 2), nullable=False)
    numero_comprobante = db.Column(db.String(255), nullable=False)
    total = db.Column(db.Numeric(8, 2), nullable=False)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    comprobante_id = db.Column(db.BigInteger, db.ForeignKey('comprobantes.id'), nullable=True)
    proveedore_id = db.Column(db.BigInteger, db.ForeignKey('proveedores.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    productos = db.relationship('CompraProducto', backref='compra', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'fecha_hora': self.fecha_hora.isoformat() if self.fecha_hora else None,
            'impuesto': float(self.impuesto) if self.impuesto else 0,
            'numero_comprobante': self.numero_comprobante,
            'total': float(self.total) if self.total else 0,
            'estado': self.estado,
            'comprobante_id': self.comprobante_id,
            'proveedore_id': self.proveedore_id,
            'comprobante': self.comprobante.to_dict() if self.comprobante else None,
            'proveedor': self.proveedor.to_dict() if self.proveedor else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }