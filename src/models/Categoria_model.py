from datetime import datetime
from decimal import Decimal
from utils.db import db


class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    caracteristica_id = db.Column(db.BigInteger, db.ForeignKey('caracteristicas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    caracteristica = db.relationship('Caracteristica', backref='categorias', lazy=True)
    productos = db.relationship("CategoriaProducto", back_populates="categoria")

    def to_dict(self):
        return {
            'id': self.id,
            'caracteristica_id': self.caracteristica_id,
            'caracteristica_nombre': self.caracteristica.nombre if self.caracteristica else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    def __repr__(self):
        return f"<Categoria(id={self.id}, caracteristica_id={self.caracteristica_id})>"