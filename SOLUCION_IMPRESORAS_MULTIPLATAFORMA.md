# 🖨️ SOLUCIÓN DE IMPRESORAS MULTIPLATAFORMA

## 🎯 EL PROBLEMA

- **Windows (desarrollo local)**: `win32print` funciona perfecto ✅
- **Linux (PythonAnywhere)**: `win32print` NO EXISTE ❌
- **Necesidad**: La app debe poder imprimir desde PythonAnywhere en impresoras del cliente

---

## 💡 LA SOLUCIÓN: PrintHost (Servidor de Impresión Local)

**Idea**: El cliente instala una aplicación pequeña en su PC Windows que:
1. **Escucha en puerto 8765** (localhost)
2. **Recibe solicitudes HTTP** desde la app
3. **Imprime localmente** con `win32print`

```
PythonAnywhere (Flask)
    │
    ├─→ HTTP POST http://cliente.local:8765/print/pedido
    │
    └─→ PrintHost (App Windows)
         │
         └─→ Impresora térmica USB
```

---

## 📋 ARQUITECTURA

### Opción A: PrintHost Local (Para clientes con servidor local)
- Cliente instala `MundoWaffles_PrintHost.exe`
- App debe estar en red (local área network)
- Flask se comunica por HTTP en puerto 8765

**Ventaja**: Simple, sin dependencias externas
**Desventaja**: Solo funciona en red local

### Opción B: PrintHost Remoto (Para clientes en diferentes redes)
- Cliente instala `MundoWaffles_PrintHost.exe`
- PrintHost se registra en servidor central con API key
- Flask consulta servidor central para encontrar clientes
- Servidor central redirecciona solicitud de impresión

**Ventaja**: Funciona desde cualquier red
**Desventaja**: Requiere servidor intermedio

---

## 🚀 IMPLEMENTACIÓN RÁPIDA (OPCIÓN A)

### Paso 1: Mejorar PrintHost (`app/printer_host.py`)

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import win32print
import logging
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
CONFIG = {
    'puerto': 8765,
    'host': '0.0.0.0',  # Escucha en toda la red local
}

# ===== HEALTHCHECK =====
@app.get('/health')
def health():
    """Verifica que PrintHost esté activo"""
    return jsonify({
        'status': 'ok',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

# ===== LISTAR IMPRESORAS =====
@app.get('/printers')
def list_printers():
    """Lista todas las impresoras disponibles en Windows"""
    try:
        printers = win32print.EnumPrinters(2)  # 2 = PRINTER_ENUM_LOCAL
        printer_list = [p[2] for p in printers]  # Obtener nombre de cada impresora
        
        return jsonify({
            'ok': True,
            'printers': printer_list,
            'count': len(printer_list)
        })
    except Exception as e:
        logger.error(f"Error listar impresoras: {e}")
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
        "content": "...",
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
        return jsonify({'ok': False, 'error': 'driver y content requeridos'}), 400
    
    try:
        logger.info(f"Imprimiendo en: {driver}")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("RAW", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            
            # Enviar contenido
            win32print.WritePrinter(hprinter, content.encode('utf-8', errors='replace'))
            
            # Avanzar papel
            if feed > 0:
                win32print.WritePrinter(hprinter, ("\n" * feed).encode('utf-8'))
            
            # Cortar papel
            if cut:
                win32print.WritePrinter(hprinter, b'\x1dV\x01')  # ESC/POS corte parcial
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Documento impreso exitosamente")
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
        "contenido": "..."
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    pedido_id = data.get('pedido_id')
    contenido = data.get('contenido', '')
    
    if not driver or not contenido:
        return jsonify({'ok': False, 'error': 'driver y contenido requeridos'}), 400
    
    try:
        logger.info(f"Imprimiendo pedido #{pedido_id} en: {driver}")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, (f"Pedido_{pedido_id}", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
            win32print.WritePrinter(hprinter, b'\n\n\n\n')
            win32print.WritePrinter(hprinter, b'\x1dV\x01')  # Corte
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Pedido #{pedido_id} impreso")
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

# ===== ERROR HANDLER =====
@app.errorhandler(404)
def not_found(e):
    return jsonify({'ok': False, 'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'ok': False, 'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    logger.info(f"🖨️ PrintHost iniciando en {CONFIG['host']}:{CONFIG['puerto']}")
    app.run(host=CONFIG['host'], port=CONFIG['puerto'], debug=False)
```

### Paso 2: Cliente HTTP en Flask para hablar con PrintHost

Crear nuevo archivo `utils/print_client.py`:

```python
"""
Cliente HTTP para comunicarse con PrintHost
Utilizado cuando la app está en PythonAnywhere
"""

import requests
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PrintHostClient:
    def __init__(self, 
                 printhost_url: str = "http://localhost:8765",
                 timeout: int = 10):
        """
        Inicializa cliente PrintHost
        
        Args:
            printhost_url: URL del servidor PrintHost (ej: http://192.168.1.100:8765)
            timeout: Timeout para requests (segundos)
        """
        self.printhost_url = printhost_url.rstrip('/')
        self.timeout = timeout
    
    def health_check(self) -> bool:
        """Verifica que PrintHost esté disponible"""
        try:
            resp = requests.get(
                f"{self.printhost_url}/health",
                timeout=self.timeout
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"PrintHost no disponible: {e}")
            return False
    
    def list_printers(self) -> list:
        """Obtiene lista de impresoras disponibles"""
        try:
            resp = requests.get(
                f"{self.printhost_url}/printers",
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('printers', [])
            return []
        except Exception as e:
            logger.error(f"Error obteniendo impresoras: {e}")
            return []
    
    def print_raw(self, 
                  driver: str,
                  content: str,
                  feed: int = 3,
                  cut: bool = True) -> Dict[str, Any]:
        """
        Imprime contenido RAW
        
        Args:
            driver: Nombre de impresora (ej: "EPSON TM-T88V Receipt5")
            content: Contenido a imprimir (texto)
            feed: Líneas de avance de papel
            cut: ¿Cortar papel?
        
        Returns:
            {'ok': bool, 'error': str (si falla)}
        """
        try:
            payload = {
                'driver': driver,
                'content': content,
                'feed': feed,
                'cut': cut
            }
            
            resp = requests.post(
                f"{self.printhost_url}/print/raw",
                json=payload,
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {'ok': False, 'error': f"Status {resp.status_code}"}
        
        except Exception as e:
            logger.error(f"Error imprimiendo: {e}")
            return {'ok': False, 'error': str(e)}
    
    def print_pedido(self,
                     driver: str,
                     pedido_id: int,
                     contenido: str) -> Dict[str, Any]:
        """Imprime un pedido"""
        try:
            payload = {
                'driver': driver,
                'pedido_id': pedido_id,
                'contenido': contenido
            }
            
            resp = requests.post(
                f"{self.printhost_url}/print/pedido",
                json=payload,
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {'ok': False, 'error': f"Status {resp.status_code}"}
        
        except Exception as e:
            logger.error(f"Error imprimiendo pedido #{pedido_id}: {e}")
            return {'ok': False, 'error': str(e)}


def get_printhost_client(app=None) -> PrintHostClient:
    """
    Obtiene cliente PrintHost
    Configurar en config.py:
    
    PRINTHOST_URL = 'http://192.168.1.100:8765'  # Producción
    """
    if app is None:
        from flask import current_app
        app = current_app
    
    printhost_url = app.config.get('PRINTHOST_URL', 'http://localhost:8765')
    return PrintHostClient(printhost_url)
```

### Paso 3: Actualizar `utils/printer.py` para usar PrintHost

```python
# Al inicio del archivo
PRINTHOST_ENABLED = not HAS_WIN32  # Usar PrintHost si NO es Windows

if PRINTHOST_ENABLED:
    from utils.print_client import PrintHostClient
    logger.info("PrintHost mode habilitado para impresión remota")

# ... en la clase ThermalPrinter

class ThermalPrinter:
    def __init__(self, printer_name=None, printhost_url=None):
        self.printer_name = printer_name
        self.printhost_url = printhost_url
        self.printer = None
        self.printhost_client = None
        
        if HAS_WIN32:
            # Modo local Windows
            if not printer_name:
                self.printer = win32print.GetDefaultPrinter()
            else:
                self.printer = printer_name
        
        elif PRINTHOST_ENABLED and printhost_url:
            # Modo remoto Linux
            self.printhost_client = PrintHostClient(printhost_url)
            logger.info(f"Usando PrintHost: {printhost_url}")
    
    def imprimir_pedido(self, pedido, cliente, items, total_con_envio):
        contenido = self._generar_recibo(pedido, cliente, items, total_con_envio)
        
        if HAS_WIN32 and self.printer:
            # Impresión local Windows
            return self._imprimir_local_windows(contenido)
        
        elif PRINTHOST_ENABLED and self.printhost_client:
            # Impresión remota via PrintHost
            return self._imprimir_remoto_printhost(
                contenido,
                pedido.id,
                tipo='pedido'
            )
        
        logger.error("No hay forma de imprimir configurada")
        return False
    
    def _imprimir_local_windows(self, contenido):
        """Imprime en Windows usando win32print"""
        try:
            hprinter = win32print.OpenPrinter(self.printer)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Recibo", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
                win32print.WritePrinter(hprinter, FEED_LINES(5))
                win32print.WritePrinter(hprinter, CUT_PAPER)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                logger.info("✅ Impreso localmente")
                return True
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            logger.error(f"❌ Error impresión local: {e}")
            return False
    
    def _imprimir_remoto_printhost(self, contenido, pedido_id, tipo='raw'):
        """Imprime remotamente via PrintHost"""
        try:
            resultado = self.printhost_client.print_raw(
                driver=self.printer_name or "EPSON TM-T88V Receipt5",
                content=contenido,
                feed=5,
                cut=True
            )
            
            if resultado.get('ok'):
                logger.info(f"✅ Impreso remotamente via PrintHost (pedido #{pedido_id})")
                return True
            else:
                logger.error(f"❌ PrintHost error: {resultado.get('error')}")
                return False
        except Exception as e:
            logger.error(f"❌ Error impresión remota: {e}")
            return False
```

### Paso 4: Actualizar `config.py`

```python
# En DevelopmentConfig
class DevelopmentConfig():
    PRINTER_NAME = 'EPSON TM-T88V Receipt5'
    PRINTHOST_URL = None  # No usar PrintHost en desarrollo

# En ProductionConfig (PythonAnywhere)
class ProductionConfig():
    PRINTER_NAME = 'EPSON TM-T88V Receipt5'
    PRINTHOST_URL = os.environ.get('PRINTHOST_URL', 'http://localhost:8765')
    # Cliente debe configurar en variables de entorno:
    # PRINTHOST_URL = http://192.168.1.100:8765
```

### Paso 5: Actualizar WSGI de PythonAnywhere

```python
# En /var/www/josephmercury10_pythonanywhere_com_wsgi.py

os.environ['PRINTHOST_URL'] = 'http://DIRECCION_IP_CLIENTE:8765'

# Ejemplo real:
# os.environ['PRINTHOST_URL'] = 'http://192.168.1.50:8765'
```

---

## 📦 DISTRIBUCIÓN DE PRINTHOST

### Generar ejecutable .exe

```bash
# En tu PC Windows
cd ~\mundowaffles_produccion\packaging

# 1. Instalar PyInstaller
pip install pyinstaller

# 2. Crear ejecutable
pyinstaller ../MundoWaffles_PrintHost.spec

# 3. Distribuir .exe a clientes
# El archivo estará en: dist/MundoWaffles_PrintHost.exe
```

---

## 🧪 TEST DE IMPRESIÓN REMOTA

### Desde PythonAnywhere (Bash Console)

```bash
# 1. Ver que PrintHost esté accesible
curl -X GET http://192.168.1.50:8765/health

# 2. Listar impresoras del cliente
curl -X GET http://192.168.1.50:8765/printers

# 3. Enviar test de impresión
curl -X POST http://192.168.1.50:8765/print/raw \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "EPSON TM-T88V Receipt5",
    "content": "TEST IMPRESSION\n\n",
    "feed": 3,
    "cut": true
  }'
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Mejorar `app/printer_host.py` con endpoints adicionales
- [ ] Crear `utils/print_client.py` para cliente HTTP
- [ ] Actualizar `utils/printer.py` para soportar ambos modos
- [ ] Actualizar `config.py` con `PRINTHOST_URL`
- [ ] Generar `MundoWaffles_PrintHost.exe`
- [ ] Crear instalador con InnoSetup
- [ ] Documentar para clientes
- [ ] Configurar `PRINTHOST_URL` en WSGI de PA

---

## 🚀 RESULTADO FINAL

**Windows (desarrollo)**:
```
app.py → utils/printer.py → win32print → Impresora USB ✅
```

**PythonAnywhere (producción)**:
```
app.py → utils/printer.py → PrintHostClient → HTTP → PrintHost.exe → Impresora USB ✅
```

**Ambos entornos funcionan con la misma lógica de negocio.** 🎉
