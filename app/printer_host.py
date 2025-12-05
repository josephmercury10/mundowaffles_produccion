"""
PrintHost - El cliente Windows hace todo el trabajo de impresión.
El servidor Flask (PythonAnywhere) solo envía instrucciones a /print/job.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import win32print
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG = {
    'puerto': 8765,
    'host': '0.0.0.0',
    'version': '4.0.0',
}


# ===== Utilidades de impresora =====
def available_printers() -> List[str]:
    try:
        return [p[2] for p in win32print.EnumPrinters(2)]
    except Exception as e:
        logger.error(f"No se pudieron listar impresoras: {e}")
        return []


def select_printer(preferred: Optional[str]) -> Optional[str]:
    printers = available_printers()
    if preferred and preferred in printers:
        return preferred
    try:
        return win32print.GetDefaultPrinter()
    except Exception as e:
        logger.error(f"Sin impresora predeterminada: {e}")
        return printers[0] if printers else None


def _print_bytes(driver: str, content: bytes, feed: int = 3, cut: bool = True, title: str = "RAW") -> Dict[str, Any]:
    if not driver:
        return {'ok': False, 'error': 'No hay impresora disponible'}

    try:
        handle = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(handle, 1, (title, None, "RAW"))
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, content)
            if feed and feed > 0:
                win32print.WritePrinter(handle, ("\n" * feed).encode('utf-8'))
            if cut:
                win32print.WritePrinter(handle, b'\x1dV\x01')
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            logger.info(f"✅ Impreso en {driver}")
            return {'ok': True, 'driver': driver}
        finally:
            win32print.ClosePrinter(handle)
    except Exception as e:
        logger.error(f"❌ Error al imprimir en {driver}: {e}")
        return {'ok': False, 'error': str(e)}


# ===== Generadores de texto =====
def _center(text: str, width: int = 42) -> str:
    return text.center(width)


def _line(char: str = '-', width: int = 42) -> str:
    return char * width


def _fmt_fecha(fecha_iso: Optional[str]) -> str:
    if not fecha_iso:
        return ""
    try:
        dt = datetime.fromisoformat(fecha_iso)
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return fecha_iso


def _format_precio(valor) -> str:
    """
    Formatea un valor numérico como precio en pesos chileno
    Ejemplo: 1000 -> $1.000, 1500000 -> $1.500.000
    """
    try:
        valor_int = int(float(valor))
        valor_str = f"{valor_int:,}".replace(",", ".")
        return f"${valor_str}"
    except (ValueError, TypeError):
        return "$0"


def build_recibo(payload: Dict[str, Any]) -> str:
    pedido = payload.get('pedido', {})
    cliente = payload.get('cliente', {})
    items = payload.get('items', [])
    total_con_envio = payload.get('total_con_envio')
    ancho = 42

    lineas = []
    lineas.append(_center("MUNDO WAFFLES", ancho))
    lineas.append(_center("Delivery", ancho))
    lineas.append(_line('=', ancho))
    lineas.append("")

    lineas.append(f"Pedido #: {pedido.get('id', '')}")
    lineas.append(f"Fecha: {_fmt_fecha(pedido.get('fecha_hora'))}")
    lineas.append("")

    lineas.append("CLIENTE:")
    if cliente:
        if cliente.get('razon_social'):
            lineas.append(f"  {cliente.get('razon_social')}")
        if cliente.get('telefono'):
            lineas.append(f"  Tel: {cliente.get('telefono')}")
        if cliente.get('direccion'):
            lineas.append(f"  Dir: {cliente.get('direccion')}")
    lineas.append("")

    lineas.append(_line('=', ancho))
    lineas.append("")
    lineas.append("ITEMS:")
    lineas.append("")

    for item in items:
        nombre = str(item.get('nombre', ''))[:30]
        cantidad = item.get('cantidad', 1)
        precio = float(item.get('precio_venta', 0))
        subtotal = float(item.get('subtotal', cantidad * precio))
        
        precio_fmt = _format_precio(precio)
        subtotal_fmt = _format_precio(subtotal)
        
        lineas.append(f"{nombre}")
        lineas.append(f"  x{cantidad} @ {precio_fmt} = {subtotal_fmt}")
        atributos = item.get('atributos', {}) or {}
        for k, v in atributos.items():
            lineas.append(f"    - {k}: {v}")
        lineas.append("")

    lineas.append(_line('=', ancho))
    lineas.append("")

    subtotal_val = float(pedido.get('total', 0))
    envio = float(pedido.get('costo_envio', 0))
    total = total_con_envio if total_con_envio is not None else subtotal_val + envio
    
    subtotal_fmt = _format_precio(subtotal_val)
    envio_fmt = _format_precio(envio)
    total_fmt = _format_precio(total)

    lineas.append(f"Subtotal:              {subtotal_fmt:>10}")
    lineas.append(f"Envio:                 {envio_fmt:>10}")
    lineas.append(_line('-', ancho))
    lineas.append(f"TOTAL:                 {total_fmt:>10}")
    lineas.append("")

    estados = {1: "EN PREPARACION", 2: "EN CAMINO", 3: "ENTREGADO"}
    estado = estados.get(pedido.get('estado_delivery'), 'DESCONOCIDO')
    lineas.append(_center(f"Estado: {estado}", ancho))
    lineas.append("")
    lineas.append(_center("Gracias por su compra!", ancho))
    lineas.append("\n\n")

    return "\n".join(lineas)


def build_comanda(payload: Dict[str, Any]) -> str:
    """
    Genera el contenido de la comanda para cocina - IDÉNTICO a utils/printer.py
    Formato:
    - Tipo de venta (MOSTRADOR/DELIVERY) en grande
    - Hora y cliente
    - Productos en letra grande
    - Mínimo papel posible
    """
    pedido = payload.get('pedido', {})
    items = payload.get('items', [])
    tipo_pedido = payload.get('tipo', 'MOSTRADOR')
    ancho = 42
    
    lineas = []
    
    # ===== ENCABEZADO COMPACTO =====
    # Tipo de venta (MOSTRADOR/DELIVERY) - centrado
    lineas.append("")
    lineas.append(_center(f"=== {tipo_pedido} ===", ancho))
    
    # Pedido #, fecha y hora en una línea
    pedido_id = pedido.get('id', '')
    fecha_hora = pedido.get('fecha_hora', '')
    if fecha_hora:
        try:
            dt = datetime.fromisoformat(fecha_hora)
            hora = dt.strftime('%H:%M')
        except:
            hora = ''
    else:
        hora = ''
    
    # Formatear pedido_id como número entero con padding
    try:
        id_num = int(pedido_id)
        lineas.append(f"#{id_num:4d}  {hora}")
    except (ValueError, TypeError):
        lineas.append(f"#{str(pedido_id):>4}  {hora}")
    
    # Cliente si disponible (en payload normalmente no viene, pero chequeamos)
    cliente = payload.get('cliente', {})
    if cliente and cliente.get('razon_social'):
        cliente_nombre = cliente.get('razon_social', '')[:20]
        lineas.append(f"CLIENTE: {cliente_nombre}")
    
    lineas.append("")
    
    # ===== PRODUCTOS (lo más importante) =====
    # Sin línea divisoria arriba para ahorrar papel
    for item in items:
        # Soportar claves en minúsculas y mayúsculas
        cantidad = item.get('cantidad') or item.get('CANTIDAD', 1)
        nombre = item.get('nombre') or item.get('NOMBRE', '')
        nombre = str(nombre).upper()[:35]
        # Formato: [cantidad]x NOMBRE (en mayúsculas para legibilidad)
        # Limitar nombre a 35 caracteres para que quepa con cantidad
        lineas.append(f"{cantidad}x {nombre}")
    
    lineas.append("")
    
    return "\n".join(lineas)


def build_agregados(payload: Dict[str, Any]) -> str:
    """Imprime comanda con productos AGREGADOS - IDÉNTICO a utils/printer.py"""
    pedido_id = payload.get('pedido_id', '')
    productos = payload.get('productos', [])
    ancho = 42
    
    lineas = []
    lineas.append("")
    lineas.append(_center("=== AGREGADOS ===", ancho))
    lineas.append(f"Pedido #{pedido_id}")
    lineas.append("")
    
    for item in productos:
        cantidad = item.get('cantidad') or item.get('CANTIDAD', 1)
        nombre = item.get('nombre') or item.get('NOMBRE', '')
        nombre = str(nombre).upper()[:35]
        lineas.append(f"{cantidad}x {nombre}")
    
    lineas.append("")
    
    return "\n".join(lineas)


def build_eliminados(payload: Dict[str, Any]) -> str:
    """Imprime comanda con productos ELIMINADOS - IDÉNTICO a utils/printer.py"""
    pedido_id = payload.get('pedido_id', '')
    productos = payload.get('productos', [])
    ancho = 42
    
    lineas = []
    lineas.append("")
    lineas.append(_center("=== ELIMINADOS ===", ancho))
    lineas.append(f"Pedido #{pedido_id}")
    lineas.append("")
    
    for item in productos:
        cantidad = item.get('cantidad') or item.get('CANTIDAD', 1)
        nombre = item.get('nombre') or item.get('NOMBRE', '')
        nombre = str(nombre).upper()[:35]
        lineas.append(f"{cantidad}x {nombre}")
    
    lineas.append("")
    
    return "\n".join(lineas)


def build_delivery(payload: Dict[str, Any]) -> str:
    """Genera el contenido del comprobante de delivery - IDÉNTICO a utils/printer.py"""
    pedido = payload.get('pedido', {})
    cliente = payload.get('cliente', {})
    productos = payload.get('productos', [])
    ancho = 42
    
    lineas = []
    
    # Título
    lineas.append("")
    lineas.append(_center("MUNDO WAFFLES", ancho))
    lineas.append(_center("=" * 20, ancho))
    lineas.append(_center("COMPROBANTE DELIVERY", ancho))
    lineas.append("")
    
    # Número de pedido, fecha y hora
    pedido_id = pedido.get('id', '')
    fecha_hora = pedido.get('fecha_hora', '')
    if fecha_hora:
        try:
            dt = datetime.fromisoformat(fecha_hora)
            fecha_str = dt.strftime('%d/%m/%Y')
            hora_str = dt.strftime('%H:%M')
        except:
            fecha_str = fecha_hora
            hora_str = ''
    else:
        fecha_str = ''
        hora_str = ''
    
    lineas.append(f"Pedido #:     {pedido_id}")
    lineas.append(f"Fecha:        {fecha_str}")
    lineas.append(f"Hora:         {hora_str}")
    lineas.append("")
    
    # Datos del cliente
    lineas.append("=" * ancho)
    lineas.append("CLIENTE")
    lineas.append("=" * ancho)
    if cliente:
        nombre = cliente.get('razon_social', 'Sin nombre')
        # Limitar nombre a ancho de ticket
        lineas.append(f"Nombre: {nombre[:35]}")
        telefono = cliente.get('telefono', 'Sin teléfono')
        lineas.append(f"Teléfono: {telefono}")
        direccion = cliente.get('direccion', 'Sin dirección')
        # Ajustar dirección a múltiples líneas si es necesario
        if len(direccion) > 35:
            lineas.append(f"Dirección: {direccion[:35]}")
            lineas.append(f"           {direccion[35:70]}")
        else:
            lineas.append(f"Dirección: {direccion}")
    else:
        lineas.append("Cliente no registrado")
    lineas.append("")
    
    # Detalle de productos
    lineas.append("=" * ancho)
    lineas.append("DETALLE DE PRODUCTOS")
    lineas.append("=" * ancho)
    
    # Calcular subtotal si vienen precios individuales
    subtotal_calculado = 0
    for item in productos:
        nombre = str(item.get('nombre', ''))
        cantidad = item.get('cantidad', 1)
        
        # Formato: "2x Waffle Nutella"
        lineas.append(f"{cantidad}x {nombre[:28]}")
        
        # Si viene precio_venta en el producto, mostrarlo
        if 'precio_venta' in item:
            precio = float(item.get('precio_venta', 0))
            item_total = cantidad * precio
            subtotal_calculado += item_total
            
            precio_fmt = _format_precio(precio)
            total_fmt = _format_precio(item_total)
            lineas.append(f"   {precio_fmt} c/u = {total_fmt}")
    
    lineas.append("")
    lineas.append("=" * ancho)
    
    # Totales
    costo_envio = float(pedido.get('costo_envio', 0))
    
    # Usar subtotal del pedido si está disponible, sino el calculado
    if pedido.get('total'):
        subtotal = float(pedido.get('total', 0))
    else:
        subtotal = subtotal_calculado
    
    total = subtotal + costo_envio
    
    subtotal_fmt = _format_precio(subtotal)
    envio_fmt = _format_precio(costo_envio)
    total_fmt = _format_precio(total)
    
    lineas.append(f"{'Subtotal:':<28} {subtotal_fmt:>11}")
    lineas.append(f"{'Envío:':<28} {envio_fmt:>11}")
    lineas.append("=" * ancho)
    lineas.append(f"{'TOTAL:':<28} {total_fmt:>11}")
    lineas.append("")
    
    # Mensaje final
    lineas.append(_center("Gracias por su preferencia!", ancho))
    lineas.append("")
    lineas.append("")
    
    return "\n".join(lineas)


# ===== Procesador de trabajos =====
def process_job(job_type: str, payload: Dict[str, Any], driver: Optional[str], feed: Optional[int], cut: Optional[bool]):
    resolved_driver = select_printer(driver)
    feed_val = 5 if feed is None else feed
    cut_val = True if cut is None else cut

    if job_type == 'raw':
        content = payload.get('content') or payload.get('contenido', '')
        if not content:
            return {'ok': False, 'error': 'content requerido'}
        return _print_bytes(resolved_driver, content.encode('utf-8', errors='replace'), feed_val, cut_val, title='RAW')

    if job_type == 'pedido':
        contenido = payload.get('contenido') or build_recibo(payload)
        return _print_bytes(resolved_driver, contenido.encode('utf-8', errors='replace'), 5, True, title='Pedido')

    if job_type == 'comanda':
        contenido = build_comanda(payload)
        logger.info(f"🔍 COMANDA GENERADA:\n{contenido}")
        logger.info(f"🔍 PAYLOAD RECIBIDO: {payload}")
        return _print_bytes(resolved_driver, contenido.encode('utf-8', errors='replace'), feed_val, cut_val, title='Comanda')

    if job_type == 'agregados':
        contenido = build_agregados(payload)
        return _print_bytes(resolved_driver, contenido.encode('utf-8', errors='replace'), feed_val, cut_val, title='Agregados')

    if job_type == 'eliminados':
        contenido = build_eliminados(payload)
        return _print_bytes(resolved_driver, contenido.encode('utf-8', errors='replace'), feed_val, cut_val, title='Eliminados')

    if job_type == 'delivery':
        contenido = build_delivery(payload)
        return _print_bytes(resolved_driver, contenido.encode('utf-8', errors='replace'), feed_val, cut_val, title='Delivery')

    return {'ok': False, 'error': f'Tipo de trabajo no soportado: {job_type}'}


# ===== Endpoints =====
@app.get('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': CONFIG['version'],
        'default_printer': select_printer(None),
        'printers': available_printers(),
        'timestamp': datetime.now().isoformat()
    })


@app.get('/printers')
def printers():
    lista = available_printers()
    return jsonify({'ok': True, 'printers': lista, 'count': len(lista)})


@app.post('/print/job')
def print_job():
    data = request.get_json(force=True, silent=True) or {}
    job_type = data.get('type', 'raw')
    payload = data.get('payload', {})
    driver = data.get('driver')
    feed = data.get('feed')
    cut = data.get('cut')
    result = process_job(job_type, payload, driver, feed, cut)
    status = 200 if result.get('ok') else 400
    return jsonify(result), status


# Compatibilidad con endpoints antiguos
@app.post('/print/raw')
def print_raw_legacy():
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    payload = {'content': data.get('content', '')}
    feed = data.get('feed')
    cut = data.get('cut')
    result = process_job('raw', payload, driver, feed, cut)
    status = 200 if result.get('ok') else 400
    return jsonify(result), status


@app.post('/print/pedido')
def print_pedido_legacy():
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    payload = {
        'contenido': data.get('contenido'),
        'pedido': {'id': data.get('pedido_id')},
    }
    result = process_job('pedido', payload, driver, None, None)
    status = 200 if result.get('ok') else 400
    return jsonify(result), status


@app.errorhandler(404)
def not_found(e):
    return jsonify({'ok': False, 'error': 'Endpoint no encontrado'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error interno: {e}")
    return jsonify({'ok': False, 'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    logger.info(f"🖨️ PrintHost v{CONFIG['version']} iniciando...")
    logger.info(f"📡 Escuchando en {CONFIG['host']}:{CONFIG['puerto']}")
    logger.info("✅ El servidor remoto solo envía /print/job")
    app.run(host=CONFIG['host'], port=CONFIG['puerto'], debug=False, use_reloader=False)
