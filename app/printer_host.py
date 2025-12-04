"""
PrintHost - Servidor de impresión térmica para Mundo Waffles
Ejecutar en Windows con: python printer_host.py
Escucha en puerto 8765 para recibir solicitudes HTTP de impresión
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import win32print
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
CONFIG = {
    'puerto': 8765,
    'host': '0.0.0.0',  # Escucha en toda la red local
    'version': '2.0.0'
}


# ===== HEALTHCHECK =====
@app.get('/health')
def health():
    """Verifica que PrintHost esté activo"""
    return jsonify({
        'status': 'ok',
        'version': CONFIG['version'],
        'timestamp': datetime.now().isoformat()
    })


# ===== LISTAR IMPRESORAS =====
@app.get('/printers')
def list_printers():
    """Lista todas las impresoras disponibles en Windows"""
    try:
        printers = win32print.EnumPrinters(2)  # 2 = PRINTER_ENUM_LOCAL
        printer_list = [p[2] for p in printers]  # Obtener nombre de cada impresora
        
        logger.info(f"✅ Impresoras disponibles: {printer_list}")
        
        return jsonify({
            'ok': True,
            'printers': printer_list,
            'count': len(printer_list)
        })
    except Exception as e:
        logger.error(f"❌ Error listar impresoras: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


# ===== IMPRIMIR RAW =====
@app.post('/print/raw')
def print_raw():
    """
    Endpoint para imprimir contenido RAW
    
    JSON esperado:
    {
        "driver": "EPSON TM-T88V Receipt5",
        "content": "Contenido a imprimir...",
        "feed": 3,
        "cut": true
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    content = data.get('content', '')
    feed = int(data.get('feed', 3))
    cut = bool(data.get('cut', True))
    
    if not driver or not content:
        logger.warning("❌ Request inválido: falta driver o content")
        return jsonify({'ok': False, 'error': 'driver y content requeridos'}), 400
    
    try:
        logger.info(f"🖨️ Imprimiendo en: {driver} (feed={feed}, cut={cut})")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("RAW", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            
            # Enviar contenido
            win32print.WritePrinter(hprinter, content.encode('utf-8', errors='replace'))
            
            # Avanzar papel
            if feed > 0:
                win32print.WritePrinter(hprinter, ("\n" * feed).encode('utf-8'))
            
            # Cortar papel (ESC/POS: GS V 1 = corte parcial)
            if cut:
                win32print.WritePrinter(hprinter, b'\x1dV\x01')
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Documento impreso exitosamente en {driver}")
            return jsonify({'ok': True})
        
        finally:
            win32print.ClosePrinter(hprinter)
    
    except Exception as e:
        logger.error(f"❌ Error al imprimir: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ===== IMPRIMIR PEDIDO =====
@app.post('/print/pedido')
def print_pedido():
    """
    Endpoint específico para imprimir pedidos
    
    JSON esperado:
    {
        "driver": "EPSON TM-T88V Receipt5",
        "pedido_id": 123,
        "contenido": "Contenido formateado del pedido..."
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    pedido_id = data.get('pedido_id')
    contenido = data.get('contenido', '')
    
    if not driver or not contenido:
        logger.warning("❌ Request inválido: falta driver o contenido")
        return jsonify({'ok': False, 'error': 'driver y contenido requeridos'}), 400
    
    try:
        logger.info(f"🧾 Imprimiendo pedido #{pedido_id} en: {driver}")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, (f"Pedido_{pedido_id}", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            
            # Contenido
            win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
            
            # Avance de papel
            win32print.WritePrinter(hprinter, b'\n\n\n\n')
            
            # Corte de papel
            win32print.WritePrinter(hprinter, b'\x1dV\x01')
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Pedido #{pedido_id} impreso exitosamente")
            return jsonify({
                'ok': True,
                'pedido_id': pedido_id,
                'mensaje': 'Pedido impreso exitosamente'
            })
        finally:
            win32print.ClosePrinter(hprinter)
    
    except Exception as e:
        logger.error(f"❌ Error pedido #{pedido_id}: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ===== ERROR HANDLERS =====
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
    logger.info("✅ Lista para recibir solicitudes de impresión")
    logger.info("💡 Configura en app.py: PRINTHOST_URL = 'http://IP:8765'")
    
    app.run(host=CONFIG['host'], port=CONFIG['puerto'], debug=False, use_reloader=False)
