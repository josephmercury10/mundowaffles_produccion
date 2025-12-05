from flask import Blueprint, request, jsonify, render_template, session, flash, make_response
from datetime import datetime
from src.models.Persona_model import Persona
from src.models.Cliente_model import Cliente
from src.models.Producto_model import Producto
from src.models.Venta_model import Venta, ProductoVenta, TipoVenta
from utils.db import db
from utils.printer import get_printer
from forms import MostradorForm

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
    producto_id = request.form.get('producto_id')
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio'))
    
    # Obtener carrito de sesión
    carrito = session.get('carrito_mostrador', {})
    
    if producto_id in carrito:
        carrito[producto_id]['cantidad'] += 1
    else:
        carrito[producto_id] = {
            'id': producto_id,
            'nombre': nombre,
            'precio': precio,
            'cantidad': 1
        }
    
    session['carrito_mostrador'] = carrito
    
    return render_carrito_mostrador()


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
        
        # Agregar productos a la venta
        for item in carrito.values():
            producto_venta = ProductoVenta(
                venta_id=venta.id,
                producto_id=int(item['id']),
                cantidad=item['cantidad'],
                precio_venta=item['precio'],
                descuento=0
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
        # Filtrar las ventas de mostrador según el estado
        # tipoventa_id=1 para mostrador
        if estado == 3:
            # "Pagados" ahora es estado de pago independiente del estado_mostrador
            ventas = Venta.query.filter(
                Venta.tipoventa_id == 1,
                Venta.comprobante_id.isnot(None)
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
