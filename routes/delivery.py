from flask import Blueprint, request, jsonify, render_template, session, flash, make_response
from datetime import datetime
import json
import uuid
from src.models.Persona_model import Persona
from src.models.Cliente_model import Cliente
from src.models.repartidores_model import Repartidor
from src.models.Producto_model import Producto, ProductoAtributo
from src.models.Venta_model import Venta
from src.models.Venta_model import ProductoVenta
from src.models.AtributoProducto_model import AtributoProducto
from src.models.ValorAtributo_model import ValorAtributo
from utils.db import db
from utils.printer import get_printer
from forms import DeliveryForm

delivery_bp = Blueprint('delivery', __name__, url_prefix='/delivery')

@delivery_bp.route('/', methods=['GET'])
def getDeliveries():
    form = DeliveryForm()
    return render_template('ventas/delivery/index.html', form=form)


# Ruta para mostrar el formulario de nuevo delivery
@delivery_bp.route('/nuevo_delivery', methods=['GET'])
def nuevo_delivery():
    form = DeliveryForm()
    form.repartidor.choices = [('', 'Seleccione...')] + [(r.id, r.persona.razon_social) for r in Repartidor.query.all()]
    return render_template('ventas/delivery/_partials/nuevo_delivery.html', form=form)


# Ruta para manejar el envío del formulario y mostrar el carrito
@delivery_bp.route('/carrito_delivery', methods=['POST'])
def save():
    form = DeliveryForm()
    form.repartidor.choices = [('', 'Seleccione...')] + [(r.id, r.persona.razon_social) for r in Repartidor.query.all()]
    
    if form.validate_on_submit():
        try:
            
            # Obtener datos del formulario
            cliente_id = request.form.get('cliente_id')
            envio = int(form.costo_envio.data.strip())
            
            # Si es nuevo cliente y se debe guardar
            if cliente_id == '':
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
                
                db.session.commit()
                
                cliente_id = cliente.id
            
            # Almacenar el cliente_id en sesión para usarlo en guardar_pedido
            if cliente_id:
                session['cliente_id'] = cliente_id
                
            cliente_data = {
                'id': cliente_id,
                'nombre': form.cliente.data,
                'telefono': form.telefono.data,
                'direccion': form.direccion.data,
            }
            
            pedido_data = {
                'tiempo_estimado': form.tiempo_estimado.data,
                'repartidor': form.repartidor.data,
                'comentarios': form.comentarios.data
            }
            

            # Inicializar carrito en sesión
            session['carrito'] = {}
            session['cliente_data'] = cliente_data
            session['pedido_data'] = pedido_data
            session['costo_envio'] = envio
            
            productos = Producto.query.filter_by(estado=1).all()

            return render_template('ventas/delivery/_partials/carrito_optimizado.html', 
                                 productos=productos, 
                                 cliente=cliente_data,
                                 carrito_items=[],
                                 pedido=pedido_data,
                                 subtotal=0,
                                 envio=envio,
                                 total=0
                                 )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Si el formulario no valida, devolver error
    return jsonify({'error': 'Formulario inválido', 'errors': form.errors}), 400


# Ruta para agregar un producto al carrito
@delivery_bp.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
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
    carrito = session.get('carrito', {})
    
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
    
    session['carrito'] = carrito
    
    # Calcular totales
    carrito_items = []
    subtotal = 0
    
    for item in carrito.values():
        item['subtotal'] = item['precio'] * item['cantidad']
        subtotal += item['subtotal']
        carrito_items.append(item)
    
    envio = session.get('costo_envio', 0)
    total = subtotal + envio

    return render_template('ventas/delivery/_partials/carrito_items.html',
                         carrito_items=carrito_items,
                         subtotal=subtotal,
                         envio=envio,
                         total=total)


# Ruta para obtener los atributos de un producto (API JSON)
@delivery_bp.route('/get_atributos_producto/<int:producto_id>')
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
@delivery_bp.route('/tiene_atributos/<int:producto_id>')
def tiene_atributos(producto_id):
    """Verifica rápidamente si un producto tiene atributos configurados"""
    count = ProductoAtributo.query.filter_by(
        producto_id=producto_id,
        es_visible=True
    ).count()
    return jsonify({'tiene_atributos': count > 0})


# Ruta para actualizar la cantidad de un producto en el carrito
@delivery_bp.route('/actualizar_cantidad', methods=['POST'])
def actualizar_cantidad():
    item_id = request.form.get('item_id')
    accion = request.form.get('accion')
    
    carrito = session.get('carrito', {})
    
    if item_id in carrito:
        if accion == 'aumentar':
            carrito[item_id]['cantidad'] += 1
        elif accion == 'disminuir':
            carrito[item_id]['cantidad'] -= 1
            if carrito[item_id]['cantidad'] <= 0:
                del carrito[item_id]
    
    session['carrito'] = carrito
    
    # Recalcular y renderizar
    return render_carrito_actualizado()


# Ruta para eliminar un producto del carrito
@delivery_bp.route('/eliminar_del_carrito/<item_id>', methods=['DELETE'])
def eliminar_del_carrito(item_id):
    carrito = session.get('carrito', {})
    if item_id in carrito:
        del carrito[item_id]
    session['carrito'] = carrito
    
    return render_carrito_actualizado()


# Función auxiliar para renderizar el carrito actualizado
def render_carrito_actualizado():
    carrito = session.get('carrito', {})
    carrito_items = []
    subtotal = 0
    
    for item in carrito.values():
        item['subtotal'] = item['precio'] * item['cantidad']
        subtotal += item['subtotal']
        carrito_items.append(item)
    
    envio = session.get('costo_envio', 0)
    total = subtotal + envio

    return render_template('ventas/delivery/_partials/carrito_items.html',
                         carrito_items=carrito_items,
                         subtotal=subtotal,
                         envio=envio,
                         total=total)


# Ruta para guardar el pedido para que quede en estado "En preparación"
@delivery_bp.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    import json
    
    try:
        carrito = session.get('carrito', {})
        cliente_data = session.get('cliente_data', {})
        pedido_data = session.get('pedido_data', {})
        envio = session.get('costo_envio', 0)
        
        if not carrito:
            return jsonify({'error': 'Carrito vacío'}), 400
        
        # Crear venta
        venta = Venta(
            fecha_hora=datetime.now(),
            impuesto=0.19,
            numero_comprobante=f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            total=sum(item['precio'] * item['cantidad'] for item in carrito.values()),
            estado=1,
            cliente_id=cliente_data.get('id'),
            user_id=1,
            tipoventa_id=2,
            estado_delivery=1,
            costo_envio=envio,
            repartidor_id=pedido_data.get('repartidor') if pedido_data.get('repartidor') else None,
            comentarios=pedido_data.get('comentarios'),
            tiempo_estimado=pedido_data.get('tiempo_estimado')
        )
        db.session.add(venta)
        db.session.flush()
        
        # Agregar productos con extras
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
            printer.imprimir_comanda_cocina(venta, items_para_imprimir, "DELIVERY")
        except Exception as e:
            # Si falla la impresión, no afecta el pedido
            print(f"Error al imprimir comanda delivery: {str(e)}")
        # ==========================================
        
        # Limpiar sesión
        session.pop('carrito', None)
        session.pop('cliente_data', None)
        session.pop('pedido_data', None)
        session.pop('costo_envio', None)

        # Respuesta con trigger para refrescar tablas
        response = make_response(
            render_template('ventas/delivery/_partials/pedido_confirmado.html',
                          venta_id=venta.id)
        )
        response.headers['HX-Trigger'] = 'refresh-pendientes'
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@delivery_bp.route('/buscar_cliente_telefono', methods=['POST'])
def buscar_cliente_telefono():
    query = request.form.get('telefono', '').strip()
    
    if not query or len(query) < 3:
        return ""
    
    # Buscar clientes que coincidan con la búsqueda por teléfono
    clientes = db.session.query(Cliente).join(Persona).filter(
        Persona.telefono.like(f'%{query}%')
    ).limit(5).all()
    
    return render_template('ventas/delivery/_partials/clientes_resultados_telefono.html', 
                           clientes=clientes, 
                           query=query)
    
    
# Seccion que se encarga de mostrar y actualizar datos de los pedidos

@delivery_bp.route('/detalle_pedido/<int:pedido_id>', methods=['GET'])
def detalle_pedido(pedido_id):
    try:
        # Obtener el pedido y sus productos
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404

        productos = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        cliente = Cliente.query.get(pedido.cliente_id)
        
        # Parsear atributos_seleccionados si es string JSON
        for producto in productos:
            if producto.atributos_seleccionados and isinstance(producto.atributos_seleccionados, str):
                try:
                    producto.atributos_seleccionados = json.loads(producto.atributos_seleccionados)
                except:
                    producto.atributos_seleccionados = []
        
        # Calcular el total incluyendo el costo de envío
        costo_envio = pedido.costo_envio if pedido.costo_envio is not None else 0
        total_con_envio = pedido.total + costo_envio

        return render_template('ventas/delivery/_partials/detalle_pedido.html',
                               pedido=pedido,
                               productos=productos,
                               total_con_envio=total_con_envio,
                               costo_envio=costo_envio,
                               cliente=cliente)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@delivery_bp.route('/pedidos_estado/<estado>', methods=['GET'])
def ventas_estado(estado):
    try:
        from datetime import datetime, date
        # Convertir el estado a un entero
        estado = int(estado)

        # Filtrar las ventas de delivery según el estado
        # tipoventa_id=2 para delivery
        query = Venta.query.filter(
            Venta.estado_delivery == estado,
            Venta.tipoventa_id == 2
        )
        
        # Si es estado 3 (entregados), filtrar solo los del día actual
        if estado == 3:
            hoy = date.today()
            query = query.filter(db.func.date(Venta.fecha_hora) == hoy)
        
        ventas = query.order_by(Venta.fecha_hora.desc()).all()

        # Renderizar un fragmento de HTML con las ventas
        return render_template('ventas/delivery/_partials/pedidos.html', ventas=ventas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@delivery_bp.route('/cambiar_estado/<int:pedido_id>/<int:nuevo_estado>', methods=['POST'])
def cambiar_estado(pedido_id, nuevo_estado):
    try:
        # Validar que el estado sea válido (1, 2 o 3)
        if nuevo_estado not in [1, 2, 3]:
            return jsonify({'error': 'Estado no válido'}), 400

        # Obtener el pedido
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404

        # Validar que no puede pasar a Enviado (2) sin haber pagado
        if nuevo_estado == 2 and pedido.comprobante_id is None:
            # Retornar error - debe pagar primero
            response = make_response(
                render_template('ventas/delivery/_partials/estado_pedido.html', 
                               pedido=pedido, 
                               error_pago='Debe cobrar el pedido antes de enviarlo')
            )
            return response

        estado_anterior = pedido.estado_delivery

        # Actualizar el estado
        pedido.estado_delivery = nuevo_estado
        db.session.commit()

        # Si se envía (estado 2), imprimir comprobante para el repartidor
        if nuevo_estado == 2:
            try:
                from flask import current_app
                cliente = Cliente.query.get(pedido.cliente_id) if pedido.cliente_id else None
                productos = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
                printer = get_printer(current_app)
                printer.imprimir_comprobante_delivery(pedido, cliente, productos)
            except Exception as e:
                print(f"Error al imprimir comprobante delivery: {str(e)}")

        # Detectar desde dónde se llamó
        hx_target = request.headers.get('HX-Target', '')
        
        # Crear respuesta con headers HX-Trigger para refrescar tablas
        if 'estado-pedido-container' in hx_target:
            # Desde detalle - devolver partial + trigger para refrescar tablas
            response = make_response(
                render_template('ventas/delivery/_partials/estado_pedido.html', pedido=pedido)
            )
        else:
            # Desde lista - respuesta vacía
            response = make_response('', 200)
        
        # Agregar trigger para refrescar las tablas afectadas
        triggers = []
        if estado_anterior == 1 or nuevo_estado == 1:
            triggers.append('refresh-pendientes')
        if estado_anterior == 2 or nuevo_estado == 2:
            triggers.append('refresh-enviados')
        if estado_anterior == 3 or nuevo_estado == 3:
            triggers.append('refresh-entregados')
        
        if triggers:
            response.headers['HX-Trigger'] = ', '.join(triggers)
        
        return response

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@delivery_bp.route('/cobrar_pedido/<int:pedido_id>', methods=['POST'])
def cobrar_pedido(pedido_id):
    """Cobra el pedido de delivery y lo marca como pagado"""
    try:
        pedido = Venta.query.get_or_404(pedido_id)
        productos = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        cliente = Cliente.query.get(pedido.cliente_id) if pedido.cliente_id else None
        
        # Obtener tipo de comprobante del formulario
        tipo_comprobante_id = request.form.get('tipo_comprobante_delivery', 1)
        metodo_pago = request.form.get(f'metodo_pago_{pedido_id}', 'efectivo')
        
        # Actualizar pedido - NO cambiar estado_delivery, solo marcar como pagado
        pedido.comprobante_id = int(tipo_comprobante_id)
        
        # Generar número de comprobante
        from src.models.Comprobante_model import Comprobante
        comprobante = Comprobante.query.get(tipo_comprobante_id)
        tipo_prefijo = "B" if str(tipo_comprobante_id) == "1" else "F"
        pedido.numero_comprobante = f"{tipo_prefijo}-{pedido.id:06d}"
        
        db.session.commit()
        
        # NO imprimir al cobrar - se imprime al enviar
        
        # Retornar el partial de estado actualizado (no vista de pago confirmado)
        costo_envio = pedido.costo_envio if pedido.costo_envio else 0
        total_con_envio = float(pedido.total) + float(costo_envio)
        
        response = make_response(
            render_template('ventas/delivery/_partials/estado_pedido.html',
                          pedido=pedido,
                          pago_exitoso=True,
                          comprobante=comprobante)
        )
        # Refrescar tabla de pendientes ya que el pedido sigue ahí pero ahora está pagado
        response.headers['HX-Trigger'] = 'refresh-pendientes'
        
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    




@delivery_bp.route('/pedido/<int:pedido_id>/producto/<int:producto_id>/actualizar', methods=['POST'])
def actualizar_producto_pedido(pedido_id, producto_id):
    """Actualiza la cantidad de un producto en un pedido en preparación"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        # Solo permitir si está en preparación
        if pedido.estado_delivery != 1:
            return jsonify({'error': 'No se puede modificar un pedido enviado'}), 403
        
        producto_venta = ProductoVenta.query.get(producto_id)
        if not producto_venta or producto_venta.venta_id != pedido_id:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        accion = request.form.get('accion')
        
        if accion == 'aumentar':
            producto_venta.cantidad += 1
        elif accion == 'disminuir':
            producto_venta.cantidad -= 1
            if producto_venta.cantidad <= 0:
                db.session.delete(producto_venta)
        
        # Recalcular total del pedido
        productos_restantes = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        pedido.total = sum(float(p.precio_venta) * p.cantidad for p in productos_restantes)
        
        db.session.commit()
        
        # Retornar el partial actualizado
        return _render_items_pedido(pedido_id)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@delivery_bp.route('/pedido/<int:pedido_id>/producto/<int:producto_id>/eliminar', methods=['DELETE'])
def eliminar_producto_pedido(pedido_id, producto_id):
    """Elimina un producto de un pedido en preparación"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado_delivery != 1:
            return jsonify({'error': 'No se puede modificar un pedido enviado'}), 403
        
        producto_venta = ProductoVenta.query.get(producto_id)
        if not producto_venta or producto_venta.venta_id != pedido_id:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        db.session.delete(producto_venta)
        
        # Recalcular total
        productos_restantes = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        pedido.total = sum(float(p.precio_venta) * p.cantidad for p in productos_restantes)
        
        db.session.commit()
        
        return _render_items_pedido(pedido_id)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def _render_items_pedido(pedido_id):
    """Función auxiliar para renderizar los items del pedido"""
    pedido = Venta.query.get(pedido_id)
    productos = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
    costo_envio = pedido.costo_envio if pedido.costo_envio else 0
    total_con_envio = float(pedido.total) + float(costo_envio)
    
    # Parsear atributos_seleccionados si es string JSON
    for producto in productos:
        if producto.atributos_seleccionados and isinstance(producto.atributos_seleccionados, str):
            try:
                producto.atributos_seleccionados = json.loads(producto.atributos_seleccionados)
            except:
                producto.atributos_seleccionados = []
    
    # Obtener carrito temporal y items pendientes de eliminar de la sesión
    carrito_temporal = session.get(f'carrito_temp_{pedido_id}', {})
    items_pendientes_eliminar = session.get(f'eliminar_{pedido_id}', [])
    
    # Convertir carrito temporal a lista con keys incluidas
    carrito_lista = []
    for key, item in carrito_temporal.items():
        item_con_key = item.copy()
        item_con_key['key'] = key
        carrito_lista.append(item_con_key)
    
    return render_template('ventas/delivery/_partials/items_pedido.html',
                          pedido=pedido,
                          productos=productos,
                          total_con_envio=total_con_envio,
                          carrito_temporal=carrito_lista,
                          items_pendientes_eliminar=items_pendientes_eliminar)
    
    
@delivery_bp.route('/pedido/<int:pedido_id>/productos_disponibles', methods=['GET'])
def productos_disponibles(pedido_id):
    """Retorna la lista de productos disponibles para agregar al pedido"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_delivery != 1:
            return '', 403
        
        # Obtener productos activos
        productos = Producto.query.filter_by(estado=1).all()
        
        return render_template('ventas/delivery/_partials/productos_disponibles.html',
                              productos=productos,
                              pedido_id=pedido_id)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@delivery_bp.route('/pedido/<int:pedido_id>/agregar_producto', methods=['POST'])
def agregar_producto_pedido(pedido_id):
    """Agrega un nuevo producto al pedido en preparación"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado_delivery != 1:
            return jsonify({'error': 'No se puede modificar un pedido enviado'}), 403
        
        producto_id = request.form.get('producto_id')
        producto = Producto.query.get(producto_id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Verificar si el producto ya existe en el pedido
        producto_existente = ProductoVenta.query.filter_by(
            venta_id=pedido_id,
            producto_id=producto_id
        ).first()
        
        if producto_existente:
            # Si ya existe, aumentar cantidad
            producto_existente.cantidad += 1
        else:
            # Si no existe, crear nuevo registro
            nuevo_producto = ProductoVenta(
                venta_id=pedido_id,
                producto_id=producto_id,
                cantidad=1,
                precio_venta=producto.precio,
                descuento=0
            )
            db.session.add(nuevo_producto)
        
        # Recalcular total del pedido
        db.session.flush()
        productos_pedido = ProductoVenta.query.filter_by(venta_id=pedido_id).all()
        pedido.total = sum(float(p.precio_venta) * p.cantidad for p in productos_pedido)
        
        db.session.commit()
        
        return _render_items_pedido(pedido_id)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== CARRITO TEMPORAL PARA AGREGAR PRODUCTOS ====================

@delivery_bp.route('/pedido/<int:pedido_id>/carrito_temp/agregar', methods=['POST'])
def carrito_temp_agregar(pedido_id):
    """Agrega un producto al carrito temporal (sin guardar en BD)"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_delivery != 1:
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
        carrito_key = f'carrito_temp_{pedido_id}'
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
        
        return _render_items_pedido(pedido_id)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@delivery_bp.route('/pedido/<int:pedido_id>/carrito_temp/aumentar/<item_key>', methods=['POST'])
def carrito_temp_aumentar(pedido_id, item_key):
    """Aumenta cantidad de un producto en el carrito temporal"""
    carrito_key = f'carrito_temp_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        carrito[item_key]['cantidad'] += 1
        session[carrito_key] = carrito
    
    return _render_items_pedido(pedido_id)


@delivery_bp.route('/pedido/<int:pedido_id>/carrito_temp/disminuir/<item_key>', methods=['POST'])
def carrito_temp_disminuir(pedido_id, item_key):
    """Disminuye cantidad de un producto en el carrito temporal"""
    carrito_key = f'carrito_temp_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        carrito[item_key]['cantidad'] -= 1
        if carrito[item_key]['cantidad'] <= 0:
            del carrito[item_key]
        session[carrito_key] = carrito
    
    return _render_items_pedido(pedido_id)


@delivery_bp.route('/pedido/<int:pedido_id>/carrito_temp/eliminar/<item_key>', methods=['POST'])
def carrito_temp_eliminar(pedido_id, item_key):
    """Elimina un producto del carrito temporal"""
    carrito_key = f'carrito_temp_{pedido_id}'
    carrito = session.get(carrito_key, {})
    
    if item_key in carrito:
        del carrito[item_key]
        session[carrito_key] = carrito
    
    return _render_items_pedido(pedido_id)


@delivery_bp.route('/pedido/<int:pedido_id>/confirmar_productos', methods=['POST'])
def confirmar_productos(pedido_id):
    """Confirma los productos del carrito temporal y los agrega al pedido"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_delivery != 1:
            return jsonify({'error': 'Pedido no válido'}), 403
        
        carrito_key = f'carrito_temp_{pedido_id}'
        carrito = session.get(carrito_key, {})
        
        if not carrito:
            return _render_items_pedido(pedido_id)
        
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
        response = make_response(_render_items_pedido(pedido_id))
        response.headers['HX-Trigger'] = 'refresh-resumen'
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== ELIMINACIÓN CON CONFIRMACIÓN ====================

@delivery_bp.route('/pedido/<int:pedido_id>/marcar_eliminar/<int:producto_id>', methods=['POST'])
def marcar_eliminar(pedido_id, producto_id):
    """Marca un producto para eliminar (sin eliminar aún)"""
    eliminar_key = f'eliminar_{pedido_id}'
    items_eliminar = session.get(eliminar_key, [])
    
    if producto_id not in items_eliminar:
        items_eliminar.append(producto_id)
        session[eliminar_key] = items_eliminar
    
    return _render_items_pedido(pedido_id)


@delivery_bp.route('/pedido/<int:pedido_id>/desmarcar_eliminar/<int:producto_id>', methods=['POST'])
def desmarcar_eliminar(pedido_id, producto_id):
    """Desmarca un producto de la lista de eliminación"""
    eliminar_key = f'eliminar_{pedido_id}'
    items_eliminar = session.get(eliminar_key, [])
    
    if producto_id in items_eliminar:
        items_eliminar.remove(producto_id)
        session[eliminar_key] = items_eliminar
    
    return _render_items_pedido(pedido_id)


@delivery_bp.route('/pedido/<int:pedido_id>/resumen_pago', methods=['GET'])
def resumen_pago(pedido_id):
    """Retorna el resumen de pago actualizado"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        return render_template('ventas/delivery/_partials/resumen_pago.html', pedido=pedido)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@delivery_bp.route('/pedido/<int:pedido_id>/confirmar_eliminacion', methods=['POST'])
def confirmar_eliminacion(pedido_id):
    """Confirma la eliminación de los productos marcados"""
    try:
        pedido = Venta.query.get(pedido_id)
        if not pedido or pedido.estado_delivery != 1:
            return jsonify({'error': 'Pedido no válido'}), 403
        
        eliminar_key = f'eliminar_{pedido_id}'
        items_eliminar = session.get(eliminar_key, [])
        
        if not items_eliminar:
            return _render_items_pedido(pedido_id)
        
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
        response = make_response(_render_items_pedido(pedido_id))
        response.headers['HX-Trigger'] = 'refresh-resumen'
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@delivery_bp.route('/imprimir_pedido/<int:pedido_id>', methods=['POST'])
def imprimir_pedido(pedido_id):
    """
    Imprime el detalle del pedido en la impresora térmica
    """
    try:
        pedido = Venta.query.get_or_404(pedido_id)
        cliente = pedido.cliente
        items = pedido.productos  # Relación con ProductoVenta
        total_con_envio = float(pedido.total) + (float(pedido.costo_envio) if pedido.costo_envio else 0)
        
        # Obtener instancia de impresora por perfil
        from utils.printer import get_printer_by_profile
        printer = get_printer_by_profile(perfil='delivery', tipo='recibo')
        
        # Imprimir
        resultado = printer.imprimir_pedido(pedido, cliente, items, total_con_envio)
        printer.cerrar()
        
        if resultado:
            return jsonify({'success': True, 'message': 'Pedido impreso exitosamente'}), 200
        else:
            return jsonify({'success': False, 'message': 'Error al imprimir'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500