from flask import Blueprint, jsonify, request
from utils.db import db
from utils.printer_manager import obtener_por_perfil
from utils.printer import ThermalPrinter
from src.models.Venta_model import Venta
from src.models.Cliente_model import Cliente

api_print_bp = Blueprint('api_print', __name__, url_prefix='/api/print')


def _build_content(tipo_doc: str, pedido: Venta):
    """
    Genera el contenido textual según tipo_doc:
    - comanda_delivery
    - comanda_mostrador
    - comprobante_delivery
    - comprobante_mostrador
    """
    from utils.printer import ThermalPrinter
    tp = ThermalPrinter(printer_name=None)  # solo para usar generadores

    if tipo_doc == 'comanda_delivery':
        productos = pedido.items  # asume relación 'items' en Venta
        return tp._generar_comanda_cocina(pedido, productos, 'DELIVERY')
    if tipo_doc == 'comanda_mostrador':
        productos = pedido.items
        return tp._generar_comanda_cocina(pedido, productos, 'MOSTRADOR')
    if tipo_doc == 'comprobante_delivery':
        cliente = Cliente.query.get(pedido.cliente_id) if getattr(pedido, 'cliente_id', None) else None
        productos = pedido.items
        return tp._generar_comprobante_delivery(pedido, cliente, productos)
    if tipo_doc == 'comprobante_mostrador':
        productos = pedido.items
        return tp._generar_recibo_mostrador(pedido, productos)
    raise ValueError('tipo_doc no soportado')


@api_print_bp.get('/pedido/<int:pedido_id>')
def get_print_payload(pedido_id: int):
    """Retorna JSON con driver_name y content para impresión local.
    Query params:
      - tipo_doc: uno de [comanda_delivery, comanda_mostrador, comprobante_delivery, comprobante_mostrador]
      - perfil: delivery|mostrador|cocina|general (para seleccionar impresora)
      - tipo_impresora: ticket|comanda|factura|cocina
      - feed (opcional), cut (opcional)
    """
    tipo_doc = request.args.get('tipo_doc')
    perfil = request.args.get('perfil', 'general')
    tipo_imp = request.args.get('tipo_impresora', 'ticket')
    feed = int(request.args.get('feed', 5))
    cut = request.args.get('cut', 'true').lower() == 'true'

    if not tipo_doc:
        return jsonify({'ok': False, 'error': 'tipo_doc requerido'}), 400

    pedido = Venta.query.get_or_404(pedido_id)

    try:
        content = _build_content(tipo_doc, pedido)
    except Exception as e:
        return jsonify({'ok': False, 'error': f'Error generando contenido: {e}'}), 500

    pr = obtener_por_perfil(perfil, tipo_imp)
    driver_name = pr.driver_name if pr else None

    if not driver_name:
        return jsonify({'ok': False, 'error': 'No hay impresora configurada para perfil/tipo'}), 400

    return jsonify({'ok': True, 'driver_name': driver_name, 'content': content, 'feed': feed, 'cut': cut})
