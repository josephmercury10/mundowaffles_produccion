from datetime import datetime
from decimal import Decimal
from utils.db import db

class Comprobante(db.Model):
    __tablename__ = 'comprobantes'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tipo_comprobante = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.BigInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_comprobante': self.tipo_comprobante,
            'estado': self.estado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

