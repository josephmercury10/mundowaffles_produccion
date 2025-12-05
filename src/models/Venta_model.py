from datetime import datetime
from utils.db import db
from src.models.Comprobante_model import Comprobante
from src.models.User_model import User

class TipoVenta(db.Model):
    __tablename__ = 'tipoventas'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    


class ProductoVenta(db.Model):
    __tablename__ = 'producto_venta'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    venta_id = db.Column(db.BigInteger, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(8, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # NUEVO CAMPO JSON
    atributos_seleccionados = db.Column(db.JSON, nullable=True)
    
    producto = db.relationship("Producto")
    
    def __repr__(self):
        return f'<ProductoVenta Venta:{self.venta_id} - Producto:{self.producto_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'precio_venta': float(self.precio_venta),
            'descuento': float(self.descuento),
            'atributos_seleccionados': self.atributos_seleccionados
        }
    
    def calcular_precio_extras(self):
        """
        Calcula el total de extras desde el JSON
        Formato: [{"id": 1, "valor": "Nutella", "precio_adicional": 500}, ...]
        """
        if not self.atributos_seleccionados:
            return 0.00
            
        total_extras = 0.00
        for extra in self.atributos_seleccionados:
            total_extras += float(extra.get('precio_adicional', 0))
        return total_extras

class Venta(db.Model):
    __tablename__ = 'ventas'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    impuesto = db.Column(db.Numeric(8, 2), nullable=False)
    numero_comprobante = db.Column(db.String(255), nullable=True)
    total = db.Column(db.Numeric(8, 2), nullable=False)
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    cliente_id = db.Column(db.BigInteger, db.ForeignKey('clientes.id'), nullable=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=True)
    comprobante_id = db.Column(db.BigInteger, db.ForeignKey('comprobantes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    tipoventa_id = db.Column(db.BigInteger, db.ForeignKey('tipoventas.id'), nullable=True)
    estado_delivery = db.Column(db.SmallInteger, nullable=False, default=1)  # 1: en preparacion, 2: enviado, 3: entregado
    estado_mostrador = db.Column(db.SmallInteger, nullable=True, default=1)  # 1: en preparacion, 2: listo
    costo_envio = db.Column(db.Numeric(10, 0), nullable=True, default=0)
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=True)
    comentarios = db.Column(db.String(50), nullable=True)
    tiempo_estimado = db.Column(db.String(15), nullable=True)
    
    # Relacion muchos a muchos con Productos a través de ProductoVenta
    productos = db.relationship("ProductoVenta")
    
    comprobante = db.relationship("Comprobante", backref="ventas")
    user = db.relationship("User", backref="ventas")
    cliente = db.relationship("Cliente", backref="ventas")
    tipoVenta = db.relationship("TipoVenta", backref="ventas")
    repartidor = db.relationship("Repartidor", backref="ventas")


    def to_dict(self):
        return {
            'id': self.id,
            'fecha_hora': self.fecha_hora.isoformat() if self.fecha_hora else None,
            'impuesto': float(self.impuesto) if self.impuesto else 0,
            'numero_comprobante': self.numero_comprobante,
            'total': float(self.total) if self.total else 0,
            'estado': self.estado,
            'cliente_id': self.cliente_id,
            'user_id': self.user_id,
            'comprobante_id': self.comprobante_id,
            'tipoventa_id': self.tipoventa_id,
            'cliente': self.cliente.to_dict() if self.cliente else None,
            'user': self.user.to_dict() if self.user else None,
            'comprobante': self.comprobante.to_dict() if self.comprobante else None,
            'tipo_venta': self.tipo_venta.to_dict() if self.tipo_venta else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }