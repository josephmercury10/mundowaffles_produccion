from datetime import datetime
from decimal import Decimal
from utils.db import db

class Presentacion(db.Model):
    __tablename__ = 'presentaciones'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    caracteristica_id = db.Column(db.BigInteger, db.ForeignKey('caracteristicas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime)
    updated_at = db.Column(db.DateTime, default=datetime, onupdate=datetime)
    
    # Relaciones
    #productos = db.relationship('Producto', backref='presentacion', lazy=True, cascade='all, delete-orphan')
    caracteristica = db.relationship('Caracteristica', backref='presentaciones', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
