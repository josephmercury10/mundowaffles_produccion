from flask import Blueprint, request, jsonify, render_template, session, flash, make_response
from datetime import datetime
from src.models.Persona_model import Persona
from src.models.Cliente_model import Cliente
from src.models.Producto_model import Producto, ProductoAtributo
from src.models.Venta_model import Venta, ProductoVenta, TipoVenta
from src.models.AtributoProducto_model import AtributoProducto
from src.models.ValorAtributo_model import ValorAtributo
from utils.db import db
from utils.printer import get_printer
from forms import MostradorForm
import json
import uuid

mostrador_bp = Blueprint('mostrador', __name__, url_prefix='/mostrador')


@mostrador_bp.route('/', methods=['GET'])
def index():
    """Vista principal del módulo mostrador"""
    form = MostradorForm()
    return render_template('ventas/mostrador/index.html', form=form)


@mostrador_bp.route('/nuevo_pedido', methods=['GET'])
def nuevo_pedido():
    """Muestra el formulario para nuevo pedido en mostrador"""
    form = MostradorForm()
    productos = Producto.query.filter_by(estado=1).all()
    return render_template('ventas/mostrador/_partials/nuevo_pedido.html', 
                         form=form, 
                         productos=productos)


@mostrador_bp.route('/crear_pedido', methods=['POST'])
def crear_pedido():
    """Crea un nuevo pedido en mostrador"""
    form = MostradorForm()
    
    if form.validate_on_submit():
        try:
            # Obtener datos del formulario
            cliente_nombre = form.cliente.data if form.cliente.data else "Cliente Mostrador"
            
            # Inicializar carrito en sesión
            session['carrito_mostrador'] = {}
            session['cliente_mostrador'] = cliente_nombre
            session['comentarios_mostrador'] = form.comentarios.data
            
            productos = Producto.query.filter_by(estado=1).all()

            return render_template('ventas/mostrador/_partials/carrito.html', 
                                 productos=productos, 
                                 cliente=cliente_nombre,
                                 carrito_items=[],
                                 subtotal=0,
                                 total=0)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Formulario inválido'}), 400


@mostrador_bp.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    """Agrega un producto al carrito del mostrador"""
    import json
    import uuid
    
    producto_id = request.form.get('producto_id')
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio'))
    precio_base = float(request.form.get('precio_base', precio))
    extras_json = request.form.get('extras', '[]')
    
    try:
        extras = json.loads(extras_json) if extras_json else []
    except:
        extras = []
    
    # Obtener carrito de sesión
    carrito = session.get('carrito_mostrador', {})
    
    # Si tiene extras, crear una entrada única para cada combinación
    if extras:
        # Crear un ID único para esta combinación producto + extras
        item_key = f"{producto_id}_{uuid.uuid4().hex[:8]}"
        
        # Construir nombre con extras
        extras_texto = ', '.join([e['valor'] for e in extras])
        nombre_completo = f"{nombre} ({extras_texto})"
        
        carrito[item_key] = {
            'id': producto_id,
            'item_key': item_key,
            'nombre': nombre_completo,
            'nombre_base': nombre,
            'precio': precio,
            'precio_base': precio_base,
            'cantidad': 1,
            'extras': extras
        }
    else:
        # Sin extras: comportamiento normal
        if producto_id in carrito and not carrito[producto_id].get('extras'):
            carrito[producto_id]['cantidad'] += 1
        else:
            carrito[producto_id] = {
                'id': producto_id,
                'item_key': producto_id,
                'nombre': nombre,
                'nombre_base': nombre,
                'precio': precio,
                'precio_base': precio,
                'cantidad': 1,
                'extras': []
            }
    
    session['carrito_mostrador'] = carrito
    
    return render_carrito_mostrador()


# Ruta para obtener los atributos de un producto (API JSON)
@mostrador_bp.route('/get_atributos_producto/<int:producto_id>')
def get_atributos_producto(producto_id):
    """Devuelve los atributos disponibles para un producto en formato JSON"""
    try:
        # Obtener la relación producto-atributos
        producto_atributos = ProductoAtributo.query.filter_by(
            producto_id=producto_id
        ).order_by(ProductoAtributo.orden_producto).all()
        
        atributos_data = []
        
        for pa in producto_atributos:
            if not pa.es_visible:
                continue
                
            atributo = pa.atributo
            if not atributo or atributo.estado != 1:
                continue
            
            # Obtener valores disponibles del atributo
            valores = ValorAtributo.query.filter_by(
                atributo_id=atributo.id,
                disponible=True,
                estado=1
            ).order_by(ValorAtributo.orden).all()
            
            valores_data = []
            for v in valores:
                valores_data.append({
                    'id': v.id,
                    'valor': v.valor,
                    'descripcion': v.descripcion or '',
                    'precio_adicional': float(v.precio_adicional or 0)
                })
            
            if valores_data:  # Solo agregar si tiene valores disponibles
                atributos_data.append({
                    'id': atributo.id,
                    'nombre': atributo.nombre,
                    'descripcion': atributo.descripcion or '',
                    'tipo': atributo.tipo,
                    'es_multiple': atributo.es_multiple,
                    'es_obligatorio': atributo.es_obligatorio,
                    'valores': valores_data
                })
        
        return jsonify({
            'success': True,
            'tiene_atributos': len(atributos_data) > 0,
            'atributos': atributos_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Ruta para verificar si un producto tiene atributos (rápido)
@mostrador_bp.route('/tiene_atributos/<int:producto_id>')
def tiene_atributos(producto_id):
    """Verifica rápidamente si un producto tiene atributos configurados"""
    count = ProductoAtributo.query.filter_by(
        producto_id=producto_id,
        es_visible=True
    ).count()
    return jsonify({'tiene_atributos': count > 0})


@mostrador_bp.route('/actualizar_cantidad', methods=['POST'])
def actualizar_cantidad():
    """Actualiza la cantidad de un producto en el carrito"""
    item_id = request.form.get('item_id')
    accion = request.form.get('accion')
    
    carrito = session.get('carrito_mostrador', {})
    
    if item_id in carrito:
        if accion == 'aumentar':
            carrito[item_id]['cantidad'] += 1
        elif accion == 'disminuir':
            carrito[item_id]['cantidad'] -= 1
            if carrito[item_id]['cantidad'] <= 0:
                del carrito[item_id]
    
    session['carrito_mostrador'] = carrito
    
    return render_carrito_mostrador()


@mostrador_bp.route('/eliminar_producto/<item_id>', methods=['DELETE'])
def eliminar_producto(item_id):
    """Elimina un producto del carrito"""
    carrito = session.get('carrito_mostrador', {})
    if item_id in carrito:
        del carrito[item_id]
    session['carrito_mostrador'] = carrito
    
    return render_carrito_mostrador()


def render_carrito_mostrador():
    """Función auxiliar para renderizar el carrito actualizado"""
    carrito = session.get('carrito_mostrador', {})
    carrito_items = []
    subtotal = 0
    
    for item in carrito.values():
        item['subtotal'] = item['precio'] * item['cantidad']
        subtotal += item['subtotal']
        carrito_items.append(item)
    
    total = subtotal  # Sin envío en mostrador

    return render_template('ventas/mostrador/_partials/carrito_items.html',
                         carrito_items=carrito_items,
                         subtotal=subtotal,
                         total=total)


@mostrador_bp.route('/guardar_pedido', methods=['POST'])
def guardar_pedido():
    """Guarda el pedido en la base de datos"""
    import json
    
    try:
        carrito = session.get('carrito_mostrador', {})
        cliente_nombre = session.get('cliente_mostrador', 'Cliente Mostrador')
        comentarios = session.get('comentarios_mostrador', '')
        
        if not carrito:
            return jsonify({'error': 'El carrito está vacío'}), 400
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
        
        # Crear la venta
        venta = Venta(
            fecha_hora=datetime.now(),
            total=total,
            impuesto=0.19,
            numero_comprobante=f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            estado=1,  # Activo
            estado_mostrador=1,  # 1=En Preparación
            estado_delivery=0,  # No aplica para mostrador
            tipoventa_id=1,  # 1=Mostrador
            comentarios=cliente_nombre
        )
        db.session.add(venta)
        db.session.flush()
        
        # Agregar productos a la venta con extras
        for item in carrito.values():
            # Serializar extras a JSON si existen
            atributos_json = None
            if item.get('extras') and len(item['extras']) > 0:
                atributos_json = json.dumps(item['extras'])
            
            # Extraer el ID real del producto (puede venir como "123" o "123_uuid")
            producto_id_real = str(item['id']).split('_')[0]
            
            producto_venta = ProductoVenta(
                venta_id=venta.id,
                producto_id=int(producto_id_real),
                cantidad=item['cantidad'],
                precio_venta=item['precio'],
                descuento=0,
                atributos_seleccionados=atributos_json
            )
            db.session.add(producto_venta)
        
        db.session.commit()
        
        # ====== IMPRIMIR COMANDA PARA COCINA ======
        try:
            from utils.printer import get_printer_by_profile
            printer = get_printer_by_profile(perfil='cocina', tipo='comanda')
            # Convertir carrito a lista para la impresora
            items_para_imprimir = list(carrito.values())
            printer.imprimir_comanda_cocina(venta, items_para_imprimir, "MOSTRADOR")
        except Exception as e:
            # Si falla la impresión, no afecta el pedido
            print(f"Error al imprimir comanda: {str(e)}")
        # ==========================================
        
        # Limpiar sesión
        session.pop('carrito_mostrador', None)
        session.pop('cliente_mostrador', None)
        session.pop('comentarios_mostrador', None)
        
        # Respuesta con trigger para refrescar tablas
        response = make_response(
            render_template('ventas/mostrador/_partials/pedido_confirmado.html', 
                          pedido=venta,
                          total=total)
        )
        response.headers['HX-Trigger'] = 'refresh-preparacion, refresh-listos'
        
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/pedidos_estado/<int:estado>', methods=['GET'])
def pedidos_estado(estado):
    """Obtiene los pedidos según su estado"""
    try:
        from datetime import datetime, date
        # Filtrar las ventas de mostrador según el estado
        # tipoventa_id=1 para mostrador
        hoy = date.today()
        
        if estado == 3:
            # "Pagados" ahora es estado de pago independiente del estado_mostrador
            # Filtrar solo los del día actual
            ventas = Venta.query.filter(
                Venta.tipoventa_id == 1,
                Venta.comprobante_id.isnot(None),
                db.func.date(Venta.fecha_hora) == hoy
            ).order_by(Venta.fecha_hora.desc()).all()
        elif estado == 2:
            # "Listos" - también filtrar solo los del día actual
            ventas = Venta.query.filter(
                Venta.estado_mostrador == estado,
                Venta.tipoventa_id == 1,
                db.func.date(Venta.fecha_hora) == hoy
            ).order_by(Venta.fecha_hora.desc()).all()
        else:
            ventas = Venta.query.filter(
                Venta.estado_mostrador == estado,
                Venta.tipoventa_id == 1
            ).order_by(Venta.fecha_hora.desc()).all()

        return render_template('ventas/mostrador/_partials/pedidos.html', ventas=ventas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/detalle_pedido/<int:pedido_id>', methods=['GET'])
def detalle_pedido(pedido_id):
    """Muestra el detalle de un pedido"""
    try:
        pedido = Venta.query.get_or_404(pedido_id)
        items = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        
        return render_template('ventas/mostrador/_partials/detalle_pedido.html',
                             pedido=pedido,
                             items=items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/cambiar_estado/<int:pedido_id>/<int:nuevo_estado>', methods=['POST'])
def cambiar_estado(pedido_id, nuevo_estado):
    """Cambia el estado de un pedido de mostrador"""
    try:
        # Validar que el estado sea válido (1=Preparación, 2=Listo)
        if nuevo_estado not in [1, 2]:
            return jsonify({'error': 'Estado no válido'}), 400

        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404

        # Reglas de negocio: para pasar a "Listo" debe estar pagado
        if nuevo_estado == 2 and not pedido.comprobante_id:
            return jsonify({'error': 'Debe estar pagado antes de marcar como Listo'}), 400

        estado_anterior = pedido.estado_mostrador

        # Actualizar el estado
        pedido.estado_mostrador = nuevo_estado
        db.session.commit()

        # Detectar desde dónde se llamó
        hx_target = request.headers.get('HX-Target', '')
        
        # Crear respuesta
        if 'estado-pedido-container' in hx_target:
            response = make_response(
                render_template('ventas/mostrador/_partials/estado_pedido.html', pedido=pedido)
            )
        else:
            response = make_response('', 200)
        
        # Agregar trigger para refrescar las tablas afectadas
        triggers = []
        if estado_anterior == 1 or nuevo_estado == 1:
            triggers.append('refresh-preparacion')
        if estado_anterior == 2 or nuevo_estado == 2:
            triggers.append('refresh-listos')
        # El estado "pagado" ahora es independiente del estado_mostrador
        
        if triggers:
            response.headers['HX-Trigger'] = ', '.join(triggers)
        
        return response

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/cobrar_pedido/<int:pedido_id>', methods=['POST'])
def cobrar_pedido(pedido_id):
    """Cobra el pedido y lo marca como pagado"""
    try:
        pedido = Venta.query.get_or_404(pedido_id)
        items = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        
        # Obtener tipo de comprobante del formulario
        tipo_comprobante_id = request.form.get('tipo_comprobante', 1)
        
        # Actualizar pago (independiente del estado_mostrador)
        pedido.comprobante_id = int(tipo_comprobante_id)
        
        # Generar número de comprobante
        from src.models.Comprobante_model import Comprobante
        comprobante = Comprobante.query.get(tipo_comprobante_id)
        tipo_prefijo = "B" if tipo_comprobante_id == 1 else "F"
        pedido.numero_comprobante = f"{tipo_prefijo}-{pedido.id:06d}"
        
        db.session.commit()
        
        # Imprimir recibo de venta
        try:
            from flask import current_app
            printer = get_printer(current_app)
            printer.imprimir_pedido_mostrador(pedido, items)
        except Exception as e:
            print(f"Error al imprimir recibo: {str(e)}")
        
        # Retornar actualización del estado y refrescar tablas
        response = make_response(
            render_template('ventas/mostrador/_partials/estado_pedido.html', pedido=pedido)
        )
        response.headers['HX-Trigger'] = 'refresh-preparacion, refresh-listos, refresh-pagados'
        
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== RUTAS PARA EDICIÓN DE PEDIDO ====================

def _render_items_pedido_mostrador(pedido_id):
    """Función auxiliar para renderizar los items del pedido mostrador"""
    pedido = Venta.query.get(pedido_id)
    productos = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
    
    # Parsear atributos_seleccionados si es string JSON
    for producto in productos:
        if producto.atributos_seleccionados and isinstance(producto.atributos_seleccionados, str):
            try:
                producto.atributos_seleccionados = json.loads(producto.atributos_seleccionados)
            except:
                producto.atributos_seleccionados = []
    
    # Obtener carrito temporal y items pendientes de eliminar de la sesión
    carrito_temporal = session.get(f'carrito_temp_mostrador_{pedido_id}', {})
    items_pendientes_eliminar = session.get(f'eliminar_mostrador_{pedido_id}', [])
    
    # Convertir carrito temporal a lista con keys incluidas
    carrito_lista = []
    for key, item in carrito_temporal.items():
        item_con_key = item.copy()
        item_con_key['key'] = key
        carrito_lista.append(item_con_key)
    
    return render_template('ventas/mostrador/_partials/items_pedido.html',
                          pedido=pedido,
                          productos=productos,
                          carrito_temporal=carrito_lista,
                          items_pendientes_eliminar=items_pendientes_eliminar)


@mostrador_bp.route('/pedido/<int:pedido_id>/items', methods=['GET'])
def items_pedido(pedido_id):
    """Retorna los items del pedido"""
    try:
        return _render_items_pedido_mostrador(pedido_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/pedido/<int:pedido_id>/resumen_pago', methods=['GET'])
def resumen_pago(pedido_id):
    """Retorna el resumen de pago actualizado"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        return render_template('ventas/mostrador/_partials/resumen_pago.html', pedido=pedido)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/pedido/<int:pedido_id>/productos_disponibles', methods=['GET'])
def productos_disponibles(pedido_id):
    """Retorna la lista de productos disponibles para agregar al pedido"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return '', 404
        
        # Solo permitir si está en preparación y no pagado
        if pedido.estado_mostrador != 1 or pedido.comprobante_id:
            return '', 403
        
        # Obtener productos activos
        productos = Producto.query.filter_by(estado=1).all()
        
        return render_template('ventas/mostrador/_partials/productos_disponibles.html',
                              productos=productos,
                              pedido_id=pedido_id)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CARRITO TEMPORAL PARA AGREGAR PRODUCTOS ====================

@mostrador_bp.route('/pedido/<int:pedido_id>/carrito_temp/agregar', methods=['POST'])
def carrito_temp_agregar(pedido_id):
    """Agrega un producto al carrito temporal (sin guardar en BD)"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_mostrador != 1 or pedido.comprobante_id:
            return jsonify({'error': 'Pedido no válido'}), 403
        
        producto_id = request.form.get('producto_id')
        nombre = request.form.get('nombre')
        precio = float(request.form.get('precio', 0))
        extras_json = request.form.get('extras', '[]')
        
        try:
            extras = json.loads(extras_json) if extras_json else []
        except:
            extras = []
        
        # Calcular precio total con extras
        precio_extras = sum(float(e.get('precio_adicional', 0)) for e in extras)
        precio_total = precio + precio_extras
        
        # Obtener carrito temporal de la sesión
        carrito_key = f'carrito_temp_mostrador_{pedido_id}'
        carrito = session.get(carrito_key, {})
        
        # Generar una clave única para cada combinación producto+extras
        item_key = f"{producto_id}_{uuid.uuid4().hex[:8]}"
        
        carrito[item_key] = {
            'id': producto_id,
            'nombre': nombre,
            'precio': precio,
            'precio_total': precio_total,
            'cantidad': 1,
            'extras': extras
        }
        
        session[carrito_key] = carrito
        
        return _render_items_pedido_mostrador(pedido_id)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/pedido/<int:pedido_id>/carrito_temp/aumentar/<item_key>', methods=['POST'])
def carrito_temp_aumentar(pedido_id, item_key):
    """Aumenta cantidad de un producto en el carrito temporal"""
    carrito_key = f'carrito_temp_mostrador_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        carrito[item_key]['cantidad'] += 1
        session[carrito_key] = carrito
    
    return _render_items_pedido_mostrador(pedido_id)


@mostrador_bp.route('/pedido/<int:pedido_id>/carrito_temp/disminuir/<item_key>', methods=['POST'])
def carrito_temp_disminuir(pedido_id, item_key):
    """Disminuye cantidad de un producto en el carrito temporal"""
    carrito_key = f'carrito_temp_mostrador_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        carrito[item_key]['cantidad'] -= 1
        if carrito[item_key]['cantidad'] <= 0:
            del carrito[item_key]
        session[carrito_key] = carrito
    
    return _render_items_pedido_mostrador(pedido_id)


@mostrador_bp.route('/pedido/<int:pedido_id>/carrito_temp/eliminar/<item_key>', methods=['POST'])
def carrito_temp_eliminar(pedido_id, item_key):
    """Elimina un producto del carrito temporal"""
    carrito_key = f'carrito_temp_mostrador_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        del carrito[item_key]
        session[carrito_key] = carrito
    
    return _render_items_pedido_mostrador(pedido_id)


@mostrador_bp.route('/pedido/<int:pedido_id>/confirmar_productos', methods=['POST'])
def confirmar_productos(pedido_id):
    """Confirma los productos del carrito temporal y los agrega al pedido"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_mostrador != 1 or pedido.comprobante_id:
            return jsonify({'error': 'Pedido no válido'}), 403
        
        carrito_key = f'carrito_temp_mostrador_{pedido_id}'
        carrito = session.get(carrito_key, {})
        
        if not carrito:
            return _render_items_pedido_mostrador(pedido_id)
        
        productos_agregados = []
        
        for item in carrito.values():
            producto_id = int(item['id'])
            extras = item.get('extras', [])
            precio_total = item.get('precio_total', item['precio'])
            
            # Siempre crear un nuevo registro para respetar los extras únicos
            nuevo_producto = ProductoVenta(
                venta_id=pedido_id,
                producto_id=producto_id,
                cantidad=item['cantidad'],
                precio_venta=precio_total,  # Precio incluye extras
                descuento=0,
                atributos_seleccionados=extras if extras else None
            )
            db.session.add(nuevo_producto)
            
            productos_agregados.append({
                'nombre': item['nombre'],
                'cantidad': item['cantidad'],
                'extras': extras
            })
        
        # Recalcular total
        db.session.flush()
        productos_pedido = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        pedido.total = sum(float(p.precio_venta) * p.cantidad for p in productos_pedido)
        
        db.session.commit()
        
        # Imprimir comanda con productos agregados
        try:
            from utils.printer import get_printer_by_profile
            printer = get_printer_by_profile(perfil='cocina', tipo='comanda')
            printer.imprimir_comanda_agregados(pedido, productos_agregados)
        except Exception as e:
            print(f"Error al imprimir comanda: {str(e)}")
        
        # Limpiar carrito temporal
        session.pop(carrito_key, None)
        
        # Retornar con trigger para actualizar resumen de pago
        response = make_response(_render_items_pedido_mostrador(pedido_id))
        response.headers['HX-Trigger'] = 'refresh-resumen'
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== ELIMINACIÓN CON CONFIRMACIÓN ====================

@mostrador_bp.route('/pedido/<int:pedido_id>/marcar_eliminar/<int:producto_id>', methods=['POST'])
def marcar_eliminar(pedido_id, producto_id):
    """Marca un producto para eliminar (sin eliminar aún)"""
    eliminar_key = f'eliminar_mostrador_{pedido_id}'
    items_eliminar = session.get(eliminar_key, [])
    
    if producto_id not in items_eliminar:
        items_eliminar.append(producto_id)
        session[eliminar_key] = items_eliminar
    
    return _render_items_pedido_mostrador(pedido_id)


@mostrador_bp.route('/pedido/<int:pedido_id>/desmarcar_eliminar/<int:producto_id>', methods=['POST'])
def desmarcar_eliminar(pedido_id, producto_id):
    """Desmarca un producto de la lista de eliminación"""
    eliminar_key = f'eliminar_mostrador_{pedido_id}'
    items_eliminar = session.get(eliminar_key, [])
    
    if producto_id in items_eliminar:
        items_eliminar.remove(producto_id)
        session[eliminar_key] = items_eliminar
    
    return _render_items_pedido_mostrador(pedido_id)


@mostrador_bp.route('/pedido/<int:pedido_id>/confirmar_eliminacion', methods=['POST'])
def confirmar_eliminacion(pedido_id):
    """Confirma la eliminación de los productos marcados"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_mostrador != 1 or pedido.comprobante_id:
            return jsonify({'error': 'Pedido no válido'}), 403
        
        eliminar_key = f'eliminar_mostrador_{pedido_id}'
        items_eliminar = session.get(eliminar_key, [])
        
        if not items_eliminar:
            return _render_items_pedido_mostrador(pedido_id)
        
        productos_eliminados = []
        
        for producto_id in items_eliminar:
            producto_venta = ProductoVenta.query.get(producto_id)
            if producto_venta and producto_venta.venta_id == pedido_id:
                productos_eliminados.append({
                    'nombre': producto_venta.producto.nombre,
                    'cantidad': producto_venta.cantidad
                })
                db.session.delete(producto_venta)
        
        # Recalcular total
        db.session.flush()
        productos_restantes = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        pedido.total = sum(float(p.precio_venta) * p.cantidad for p in productos_restantes)
        
        db.session.commit()
        
        # Imprimir comanda de eliminación
        try:
            from utils.printer import get_printer_by_profile
            printer = get_printer_by_profile(perfil='cocina', tipo='comanda')
            printer.imprimir_comanda_eliminados(pedido, productos_eliminados)
        except Exception as e:
            print(f"Error al imprimir comanda eliminación: {str(e)}")
        
        # Limpiar lista de eliminación
        session.pop(eliminar_key, None)
        
        # Retornar con trigger para actualizar resumen de pago
        response = make_response(_render_items_pedido_mostrador(pedido_id))
        response.headers['HX-Trigger'] = 'refresh-resumen'
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@mostrador_bp.route('/imprimir_pedido/<int:pedido_id>', methods=['POST'])
def imprimir_pedido(pedido_id):
    """Imprime el pedido en la impresora térmica"""
    try:
        pedido = Venta.query.get_or_404(pedido_id)
        items = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        
        # Obtener instancia de impresora por perfil
        from utils.printer import get_printer_by_profile
        printer = get_printer_by_profile(perfil='mostrador', tipo='venta')
        
        # Imprimir (usando método simplificado para mostrador)
        resultado = printer.imprimir_pedido_mostrador(pedido, items)
        printer.cerrar()
        
        if resultado:
            return jsonify({'success': True, 'message': 'Pedido impreso exitosamente'}), 200
        else:
            return jsonify({'success': False, 'message': 'Error al imprimir'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
