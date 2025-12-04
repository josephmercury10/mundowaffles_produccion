from datetime import datetime
from decimal import Decimal
from utils.db import db

class Documento(db.Model):
    __tablename__ = 'documentos'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tipo_documento = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacion 1 a N con la tabla Personas
    personas = db.relationship('Persona', backref='documento', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_documento': self.tipo_documento,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }