from datetime import datetime
from utils.db import db

class ValorAtributo(db.Model):
    """
    Modelo para la tabla valores_atributo
    Define los valores específicos que puede tener cada atributo
    """
    __tablename__ = 'valores_atributo'
    
    id = db.Column(db.BigInteger, primary_key=True)
    atributo_id = db.Column(db.BigInteger, db.ForeignKey('atributos_producto.id'), nullable=False)
    valor = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    precio_adicional = db.Column(db.Numeric(10, 2), default=0.00)
    disponible = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ValorAtributo {self.valor}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'atributo_id': self.atributo_id,
            'valor': self.valor,
            'descripcion': self.descripcion,
            'precio_adicional': float(self.precio_adicional),
            'disponible': self.disponible,
            'orden': self.orden,
            'estado': self.estado
        }