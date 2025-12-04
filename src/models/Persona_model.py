from datetime import datetime
from decimal import Decimal
from utils.db import db

class Persona(db.Model):
    __tablename__ = 'personas'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    razon_social = db.Column(db.String(80), nullable=False)
    direccion = db.Column(db.String(80), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    tipo_persona = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    documento_id = db.Column(db.BigInteger, db.ForeignKey('documentos.id'), nullable=False, unique=True)
    numero_documento = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacion 1 a N con la tabla clientes:
    clientes = db.relationship('Cliente', backref='persona', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'razon_social': self.razon_social,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'tipo_persona': self.tipo_persona,
            'estado': self.estado,
            'documento_id': self.documento_id,
            'documento': self.documento.to_dict() if self.documento else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }