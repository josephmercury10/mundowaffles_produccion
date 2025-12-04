from flask import Blueprint, jsonify, render_template, request, session, json
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from forms import DeliveryForm
from src.models.Producto_model import Producto
from src.models.Venta_model import Venta, ProductoVenta
from src.models.Cliente_model import Cliente
from src.models.Persona_model import Persona
from utils.db import db

pruebas_bp = Blueprint('pruebas', __name__, url_prefix='/pruebas')

@pruebas_bp.route('/')
def prueba():
    form = DeliveryForm()
    return render_template('ventas/prueba.html', form=form)

@pruebas_bp.route('/nuevo_pedido', methods=['GET'])
def nuevo_pedido():
    form = DeliveryForm()
    return render_template('ventas/_partials/nuevo_pedido.html', form=form)

@pruebas_bp.route('/buscar_cliente_telefono', methods=['POST'])
def buscar_cliente_telefono():
    query = request.form.get('telefono', '').strip()
    
    if not query or len(query) < 3:
        return ""
    
    # Buscar clientes que coincidan con la búsqueda por teléfono
    clientes = db.session.query(Cliente).join(Persona).filter(
        Persona.telefono.like(f'%{query}%')
    ).limit(5).all()
    
    return render_template('ventas/_partials/clientes_resultados_telefono.html', 
                           clientes=clientes, 
                           query=query)
    
    

# Vista para mostrar el detalle del pedido editable
@pruebas_bp.route('/detalle_pedido/<int:venta_id>', methods=['GET'])
def detalle_pedido(venta_id):
    try: 
        # Obtener la venta con sus relaciones
        venta = (Venta.query
                 .options(
                     joinedload(Venta.productos).joinedload(ProductoVenta.producto),
                     joinedload(Venta.cliente)
                 )
                 .get(venta_id))
        
        if not venta:
            return jsonify({'error': 'Pedido no encontrado'}), 404

        # Obtener todos los productos disponibles para agregar
        productos_disponibles = Producto.query.filter_by(estado=1).all()

        # Normalizar datos del cliente
        cliente_data = {
            'id': venta.cliente_id or '',
            'nombre': '',
            'telefono': '',
            'direccion': ''
        }
        
        if venta.cliente:
            # Intentar obtener datos del cliente desde diferentes fuentes
            persona = getattr(venta.cliente, 'persona', None)
            if persona:
                cliente_data.update({
                    'nombre': (getattr(persona, 'nombres', None) or 
                              getattr(persona, 'razon_social', None) or 
                              'Sin nombre'),
                    'telefono': getattr(persona, 'telefono', ''),
                    'direccion': getattr(persona, 'direccion', '')
                })
            else:
                cliente_data.update({
                    'nombre': getattr(venta.cliente, 'nombre', 'Sin nombre'),
                    'telefono': getattr(venta.cliente, 'telefono', ''),
                    'direccion': getattr(venta.cliente, 'direccion', '')
                })

        # Convertir los items a formato JSON para JavaScript
        items_json = []
        for pv in venta.productos:
            prod = getattr(pv, 'producto', None)
            items_json.append({
                'id': str(pv.producto_id),  # Convertir a string para usar como clave
                'nombre': getattr(prod, 'nombre', 'Producto'),
                'precio': float(pv.precio_venta),
                'cantidad': int(pv.cantidad),
                'subtotal': float(pv.precio_venta) * int(pv.cantidad)
            })

        # Calcular totales
        subtotal = sum(item['subtotal'] for item in items_json)
        envio = 1000  # Costo fijo de envío
        total = subtotal + envio

        return render_template(
            'ventas/_partials/detalle_pedido_editable.html',
            venta=venta,
            cliente=cliente_data,
            items=items_json, 
            productos_disponibles=productos_disponibles,
            subtotal=subtotal,
            envio=envio,
            total=total
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pruebas_bp.route('/save', methods=['POST'])
def save():
    form = DeliveryForm()
    if form.validate_on_submit():
        try:
            # Obtener datos del formulario
            cliente_id = request.form.get('cliente_id')
            es_nuevo_cliente = request.form.get('es_nuevo_cliente') == '1'
            guardar_cliente = request.form.get('checkDefault') == 'on'
            
            # Si es nuevo cliente y se debe guardar
            if es_nuevo_cliente and guardar_cliente:
                # Crear nueva persona
                persona = Persona(
                    razon_social=form.cliente.data,
                    direccion=form.direccion.data,
                    telefono=form.telefono.data,
                    tipo_persona="Persona natural",
                    documento_id=1,  # Valor por defecto
                    numero_documento="Sin documento"  # Valor por defecto
                )
                db.session.add(persona)
                db.session.flush()  # Para obtener el ID
                
                # Crear nuevo cliente
                cliente = Cliente(
                    persona_id=persona.id
                )
                db.session.add(cliente)
                db.session.flush()
                
                cliente_id = cliente.id
            
            # Almacenar el cliente_id en sesión para usarlo en guardar_pedido
            if cliente_id:
                session['cliente_id'] = cliente_id
            
            # Obtener productos para mostrar en la siguiente vista
            productos = Producto.query.all()
            
            # Guardar datos del cliente para mostrar en el carrito
            cliente_data = {
                'id': cliente_id,
                'nombre': form.cliente.data,
                'telefono': form.telefono.data,
                'direccion': form.direccion.data,
                'costo_envio': form.costo_envio.data,
                'tiempo_estimado': form.tiempo_estimado.data,
                'comentarios': form.comentarios.data,
                'repartidor': form.repartidor.data
            }
            
            return render_template('ventas/_partials/carrito.html', 
                                  form=form, 
                                  productos=productos, 
                                  cliente=cliente_data)
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'errors': form.errors}), 400



@pruebas_bp.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    producto_id = request.form.get('id')
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    #print(f"Producto ID: {producto_id}, Nombre: {nombre}, Precio: {precio}")
    ventas = Venta.query.all()

    return render_template('ventas/_partials/producto_item.html',
                         producto={
                             'id': producto_id,
                             'nombre': nombre,
                             'precio': precio
                         })
    
    
@pruebas_bp.route('/guardar_pedido', methods=['POST'])
def guardar_pedido():
    try:
        data = request.get_json()
        productos = data['productos']
        
        # Obtener el cliente_id de la sesión
        cliente_id = session.get('cliente_id')
        
        # Crear la venta
        venta = Venta(
            fecha_hora=db.func.current_timestamp(),
            impuesto=0.19,
            numero_comprobante=f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            total=sum(float(p['precio']) * int(p['cantidad']) for p in productos),
            estado=1,
            cliente_id=cliente_id,  # Usar el cliente_id guardado
            user_id=1,  # Ejemplo o desde sesión si tienes autenticación
            tipoventa_id=2  # Venta delivery
        )
        db.session.add(venta)
        db.session.flush()  # Para obtener el ID de la venta
        
        # Crear los productos de la venta
        for producto in productos:
            producto_venta = ProductoVenta(
                venta_id=venta.id,
                producto_id=producto['id'],
                cantidad=producto['cantidad'],
                precio_venta=producto['precio'],
                descuento=0
            )
            db.session.add(producto_venta)
        
        db.session.commit()
        
        # Limpiar el cliente_id de la sesión
        session.pop('cliente_id', None)
        
        return jsonify({
            'success': True,
            'message': 'Pedido guardado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })
        

@pruebas_bp.route('/ventas_estado/<estado>', methods=['GET'])
def ventas_estado(estado):
    try:
        # Convertir el estado a un entero
        estado = int(estado)

        # Filtrar las ventas según el estado
        ventas = Venta.query.filter_by(estado_delivery=estado).all()

        # Renderizar un fragmento de HTML con las ventas
        return render_template('ventas/_partials/ventas_table.html', ventas=ventas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# Filtro personalizado para formatear fechas como "hace X tiempo"
@pruebas_bp.app_template_filter('timeago')
def timeago_filter(date):
    if not date:
        return "Sin fecha"
    
    now = datetime.now()
    diff = now - date
    
    # Obtener total de segundos
    seconds = int(diff.total_seconds())
    
    # Convertir a formato legible
    if seconds < 60:
        return f"{seconds} seg"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} min"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}min"
    elif seconds < 604800:  # 7 días
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"
    else:
        # Para periodos más largos, mostrar la fecha completa
        return date.strftime("%d/%m/%Y")