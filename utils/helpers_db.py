from datetime import datetime
from models.AtributoProducto_model import AtributoProducto
from models.ValorAtributo_model import ValorAtributo
from models.Producto_model import ProductoAtributo, Producto, ProductoVenta
from utils.db import db
# ==========================================
# MÉTODOS HELPER PARA LOS MODELOS
# ==========================================

class AtributoProducto(AtributoProducto):
    """
    Extensión del modelo con métodos útiles
    """
    
    @classmethod
    def get_activos(cls):
        """Obtener solo atributos activos"""
        return cls.query.filter_by(estado=1).order_by(cls.orden).all()
    
    @classmethod
    def get_por_tipo(cls, tipo):
        """Obtener atributos por tipo (extra, variante, opcion)"""
        return cls.query.filter_by(tipo=tipo, estado=1).order_by(cls.orden).all()
    
    def get_valores_disponibles(self):
        """Obtener valores disponibles de este atributo"""
        return ValorAtributo.query.filter_by(
            atributo_id=self.id,
            disponible=True,
            estado=1
        ).order_by(ValorAtributo.orden).all()

class ValorAtributo(ValorAtributo):
    """
    Extensión del modelo con métodos útiles
    """
    
    @classmethod
    def get_por_atributo(cls, atributo_id):
        """Obtener valores por atributo"""
        return cls.query.filter_by(
            atributo_id=atributo_id,
            disponible=True,
            estado=1
        ).order_by(cls.orden).all()

# ==========================================
# FUNCIONES HELPER PARA USAR EN TUS VISTAS
# ==========================================

def obtener_atributos_producto(producto_id):
    """
    Obtiene todos los atributos disponibles para un producto específico
    """
    query = db.session.query(
        AtributoProducto,
        ValorAtributo
    ).join(
        ProductoAtributo, AtributoProducto.id == ProductoAtributo.atributo_id
    ).join(
        ValorAtributo, AtributoProducto.id == ValorAtributo.atributo_id
    ).filter(
        ProductoAtributo.producto_id == producto_id,
        ProductoAtributo.es_visible == True,
        AtributoProducto.estado == 1,
        ValorAtributo.disponible == True,
        ValorAtributo.estado == 1
    ).order_by(
        ProductoAtributo.orden_producto,
        AtributoProducto.orden,
        ValorAtributo.orden
    ).all()
    
    # Agrupar por atributo
    atributos_dict = {}
    for atributo, valor in query:
        if atributo.id not in atributos_dict:
            atributos_dict[atributo.id] = {
                'atributo': atributo.to_dict(),
                'valores': []
            }
        atributos_dict[atributo.id]['valores'].append(valor.to_dict())
    
    return list(atributos_dict.values())

def calcular_precio_con_atributos(producto_id, atributos_seleccionados):
    """
    Calcula el precio final de un producto con sus atributos seleccionados
    """    
    producto = Producto.query.get(producto_id)
    if not producto:
        return None
    
    precio_base = float(producto.precio)
    precio_extras = 0.00
    
    for atributo in atributos_seleccionados:
        for valor in atributo.get('valores', []):
            precio_extras += float(valor.get('precio', 0))
    
    return precio_base + precio_extras

def crear_producto_venta_con_atributos(venta_id, producto_id, cantidad, atributos_seleccionados):
    """
    Crea un registro ProductoVenta con atributos seleccionados
    """
    # Calcular precio con atributos
    precio_total = calcular_precio_con_atributos(producto_id, atributos_seleccionados)
    
    if precio_total is None:
        raise ValueError(f"Producto {producto_id} no encontrado")
    
    # Crear el registro
    producto_venta = ProductoVenta(
        venta_id=venta_id,
        producto_id=producto_id,
        cantidad=cantidad,
        precio_venta=precio_total,
        atributos_seleccionados=atributos_seleccionados
    )
    
    db.session.add(producto_venta)
    return producto_venta