from utils.db import db
from datetime import datetime

class Marca(db.Model):
    __tablename__ = 'marcas'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    caracteristica_id = db.Column(db.BigInteger, db.ForeignKey('caracteristicas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    caracteristica = db.relationship('Caracteristica', backref='marcas', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'caracteristica_id': self.caracteristica_id,
            'caracteristica_nombre': self.caracteristica.nombre if self.caracteristica else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }