from datetime import datetime
from utils.db import db

class AtributoProducto(db.Model):

    __tablename__ = 'atributos_producto'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255), nullable=True)
    tipo = db.Column(db.Enum('extra', 'variante', 'opcion'), default='extra')
    es_multiple = db.Column(db.Boolean, default=False)
    es_obligatorio = db.Column(db.Boolean, default=False)
    orden = db.Column(db.Integer, default=0)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    valores = db.relationship('ValorAtributo', backref='atributo', lazy=True, cascade='all, delete-orphan')
    productos = db.relationship('ProductoAtributo', backref='atributo', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AtributoProducto {self.nombre}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'es_multiple': self.es_multiple,
            'es_obligatorio': self.es_obligatorio,
            'orden': self.orden,
            'estado': self.estado
        }
        

