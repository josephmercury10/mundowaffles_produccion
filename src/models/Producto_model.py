from datetime import datetime
from decimal import Decimal
from utils.db import db

class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'
    
    id = db.Column(db.BigInteger, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    producto_id = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
    categoria_id = db.Column(db.BigInteger, db.ForeignKey('categorias.id'), nullable=False)
    
    # Relaciones directas
    producto = db.relationship("Producto", back_populates="categorias")
    categoria = db.relationship("Categoria", back_populates="productos")


class ProductoAtributo(db.Model):
    """Tabla pivote que relaciona productos con sus atributos/extras disponibles"""
    __tablename__ = 'producto_atributo'
    
    id = db.Column(db.BigInteger, primary_key=True)
    producto_id = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
    atributo_id = db.Column(db.BigInteger, db.ForeignKey('atributos_producto.id'), nullable=False)
    es_visible = db.Column(db.Boolean, default=True)
    orden_producto = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Restricción única
    __table_args__ = (
        db.UniqueConstraint('producto_id', 'atributo_id', name='producto_atributo_unique'),
    )
    
    # Relaciones
    producto = db.relationship("Producto", back_populates="atributos")
    atributo = db.relationship("AtributoProducto", backref="producto_atributos")
    
    def __repr__(self):
        return f'<ProductoAtributo Producto:{self.producto_id} - Atributo:{self.atributo_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'atributo_id': self.atributo_id,
            'es_visible': self.es_visible,
            'orden_producto': self.orden_producto
        }


class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    descripcion = db.Column(db.String(255), nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    img_path = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    marca_id = db.Column(db.BigInteger, db.ForeignKey('marcas.id'), nullable=False)
    presentacione_id = db.Column(db.BigInteger, db.ForeignKey('presentaciones.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    categorias = db.relationship("CategoriaProducto", back_populates="producto")
    atributos = db.relationship("ProductoAtributo", back_populates="producto", lazy='dynamic')
    marca = db.relationship("Marca")
    presentacion = db.relationship("Presentacion")
    
    def tiene_extras(self):
        """Verifica si el producto tiene extras/atributos configurados"""
        return self.atributos.filter_by(es_visible=True).count() > 0
    
    def get_extras(self):
        """Obtiene los extras/atributos del producto con sus valores"""
        from src.models.AtributoProducto_model import AtributoProducto
        from src.models.ValorAtributo_model import ValorAtributo
        
        extras = []
        for pa in self.atributos.filter_by(es_visible=True).order_by(ProductoAtributo.orden_producto):
            atributo = AtributoProducto.query.get(pa.atributo_id)
            if atributo and atributo.estado == 1:
                valores = ValorAtributo.query.filter_by(
                    atributo_id=atributo.id,
                    disponible=True,
                    estado=1
                ).order_by(ValorAtributo.orden).all()
                
                extras.append({
                    'atributo': atributo.to_dict(),
                    'valores': [v.to_dict() for v in valores]
                })
        return extras

    def __repr__(self):
        return f"<Producto(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}')>"