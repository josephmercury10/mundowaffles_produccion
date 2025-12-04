# 🖨️ PRINTHOST REMOTO - Opción B (Recomendada)

## 📋 DESCRIPCIÓN

Sistema de impresión remota que funciona **desde cualquier red**:

- ✅ Cliente (Windows) instala `MundoWaffles_PrintHost.exe`
- ✅ PrintHost se registra en **servidor central** con un código único
- ✅ PythonAnywhere consulta servidor central para encontrar cliente
- ✅ Servidor central redirecciona solicitud de impresión
- ✅ **Funciona incluso si cliente está en diferente red/ciudad**

---

## 🏗️ ARQUITECTURA

```
┌─────────────────────┐
│  PythonAnywhere     │
│  (Nube, app Flask)  │
│                     │
│  Cliente HTTP       │
│  "Imprimir pedido"  │
└──────────┬──────────┘
           │
           │ (1) Consulta
           │ /api/find-client?code=ABC123
           │
           ▼
┌─────────────────────────────────────────┐
│  Servidor Central (PrintHost Registry)  │
│  (Tu servidor o API pública)            │
│                                         │
│  - Base datos de clientes registrados   │
│  - Tokens/Códigos únicos                │
│  - URLs de PrintHost activos            │
└────────┬────────────────────────────────┘
         │
         │ (2) Responde
         │ http://192.168.1.50:8765
         │
         ▼
┌─────────────────────────┐
│  Cliente (Windows)      │
│                         │
│  PrintHost.exe          │
│  (escucha puerto 8765)  │
│                         │
│  (3) Recibe solicitud   │
│  de impresión           │
│                         │
│  win32print →           │
│  Impresora USB ✅       │
└─────────────────────────┘
```

---

## 🚀 IMPLEMENTACIÓN PASO A PASO

### PASO 1: Crear Servidor Central (PrintHost Registry)

Crear archivo `printhost_registry.py` en tu servidor (o usar supabase/firebase):

```python
"""
PrintHost Registry - Servidor central que gestiona impresoras remotas
Ejecutar en: tu servidor o en PythonAnywhere account separada
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# En producción, usar base de datos real (PostgreSQL, etc)
# Por ahora, diccionario en memoria
REGISTERED_CLIENTS = {}

class PrintClient:
    def __init__(self, code, ip, port=8765):
        self.code = code
        self.ip = ip
        self.port = port
        self.registered_at = datetime.now()
        self.last_ping = datetime.now()
        self.status = 'active'
    
    def to_dict(self):
        return {
            'code': self.code,
            'url': f'http://{self.ip}:{self.port}',
            'status': self.status,
            'last_ping': self.last_ping.isoformat()
        }

# ===== REGISTRO DE CLIENTE =====
@app.post('/api/register')
def register_client():
    """
    Cliente PrintHost se registra
    
    Esperado:
    {
        "ip": "192.168.1.50",
        "port": 8765
    }
    
    Devuelve:
    {
        "code": "ABC-123-DEF",
        "url": "http://192.168.1.50:8765"
    }
    """
    data = request.get_json() or {}
    ip = data.get('ip')
    port = data.get('port', 8765)
    
    if not ip:
        return jsonify({'ok': False, 'error': 'ip requerido'}), 400
    
    try:
        # Generar código único
        code = str(uuid.uuid4())[:8].upper()
        
        # Crear cliente
        client = PrintClient(code, ip, port)
        REGISTERED_CLIENTS[code] = client
        
        print(f"✅ Cliente registrado: {code} ({ip}:{port})")
        
        return jsonify({
            'ok': True,
            'code': code,
            'message': f'Registrado exitosamente con código {code}'
        })
    
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ===== ENCONTRAR CLIENTE =====
@app.get('/api/find-client/<code>')
def find_client(code):
    """
    PythonAnywhere consulta: ¿dónde está el PrintHost ABC-123?
    
    Devuelve:
    {
        "ok": true,
        "url": "http://192.168.1.50:8765"
    }
    """
    client = REGISTERED_CLIENTS.get(code.upper())
    
    if not client:
        return jsonify({
            'ok': False,
            'error': f'Cliente {code} no encontrado'
        }), 404
    
    if client.status != 'active':
        return jsonify({
            'ok': False,
            'error': f'Cliente {code} no está activo'
        }), 503
    
    # Actualizar ping
    client.last_ping = datetime.now()
    
    return jsonify({
        'ok': True,
        'code': code,
        'url': f'http://{client.ip}:{client.port}'
    })

# ===== HEALTHCHECK =====
@app.get('/api/health')
def health():
    active_clients = sum(1 for c in REGISTERED_CLIENTS.values() if c.status == 'active')
    return jsonify({
        'status': 'ok',
        'registered_clients': len(REGISTERED_CLIENTS),
        'active_clients': active_clients,
        'timestamp': datetime.now().isoformat()
    })

# ===== LISTA DE CLIENTES (ADMIN) =====
@app.get('/api/clients')
def list_clients():
    """Admin: ver todos los clientes registrados"""
    clients = [c.to_dict() for c in REGISTERED_CLIENTS.values()]
    return jsonify({
        'total': len(clients),
        'clients': clients
    })

# ===== LIMPIAR CLIENTES INACTIVOS =====
@app.post('/api/cleanup')
def cleanup():
    """Eliminar clientes que no han hecho ping en 1 hora"""
    cutoff = datetime.now() - timedelta(hours=1)
    removed = []
    
    for code, client in list(REGISTERED_CLIENTS.items()):
        if client.last_ping < cutoff:
            removed.append(code)
            del REGISTERED_CLIENTS[code]
    
    return jsonify({
        'removed': removed,
        'total_active': len(REGISTERED_CLIENTS)
    })

if __name__ == '__main__':
    print("📡 PrintHost Registry iniciando...")
    print("🖨️ Endpoints disponibles:")
    print("  - POST /api/register (cliente se registra)")
    print("  - GET /api/find-client/<code> (buscar cliente)")
    print("  - GET /api/health (estado del servidor)")
    print("  - GET /api/clients (listar clientes)")
    print("  - POST /api/cleanup (limpiar inactivos)")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

### PASO 2: Actualizar PrintHost en Cliente Windows

Modificar `app/printer_host.py` para registrarse en servidor central:

```python
"""
PrintHost v2.1 - Con soporte para Registro Central (Opción B)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import win32print
import logging
import requests
import os
from datetime import datetime
import socket

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
CONFIG = {
    'puerto': 8765,
    'host': '0.0.0.0',
    'version': '2.1.0',
    'registry_url': os.environ.get('REGISTRY_URL', 'http://localhost:5000'),  # Servidor central
    'client_code': None  # Se obtiene al registrarse
}

# ===== OBTENER IP LOCAL =====
def get_local_ip():
    """Obtiene IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ===== REGISTRAR EN SERVIDOR CENTRAL =====
def register_to_registry():
    """Registra este PrintHost en el servidor central"""
    try:
        local_ip = get_local_ip()
        
        payload = {
            'ip': local_ip,
            'port': CONFIG['puerto']
        }
        
        resp = requests.post(
            f"{CONFIG['registry_url']}/api/register",
            json=payload,
            timeout=5
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok'):
                code = data.get('code')
                CONFIG['client_code'] = code
                logger.info(f"✅ Registrado en servidor central con código: {code}")
                logger.info(f"📡 URL accesible desde: http://{local_ip}:{CONFIG['puerto']}")
                return code
        
        logger.warning(f"⚠️ Fallo en registro: Status {resp.status_code}")
        return None
    
    except Exception as e:
        logger.warning(f"⚠️ Servidor central no disponible: {e}")
        logger.info("💡 Funcionando en modo local")
        return None

# ===== HEALTHCHECK =====
@app.get('/health')
def health():
    """Verifica que PrintHost esté activo"""
    return jsonify({
        'status': 'ok',
        'version': CONFIG['version'],
        'code': CONFIG['client_code'],
        'timestamp': datetime.now().isoformat()
    })

# ===== LISTAR IMPRESORAS =====
@app.get('/printers')
def list_printers():
    """Lista todas las impresoras disponibles"""
    try:
        printers = win32print.EnumPrinters(2)
        printer_list = [p[2] for p in printers]
        
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
    """Imprime contenido RAW"""
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    content = data.get('content', '')
    feed = int(data.get('feed', 3))
    cut = bool(data.get('cut', True))
    
    if not driver or not content:
        return jsonify({'ok': False, 'error': 'driver y content requeridos'}), 400
    
    try:
        logger.info(f"🖨️ Imprimiendo en: {driver}")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("RAW", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, content.encode('utf-8', errors='replace'))
            
            if feed > 0:
                win32print.WritePrinter(hprinter, ("\n" * feed).encode('utf-8'))
            
            if cut:
                win32print.WritePrinter(hprinter, b'\x1dV\x01')
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Impreso exitosamente")
            return jsonify({'ok': True})
        
        finally:
            win32print.ClosePrinter(hprinter)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

# ===== IMPRIMIR PEDIDO =====
@app.post('/print/pedido')
def print_pedido():
    """Imprime un pedido"""
    data = request.get_json(force=True, silent=True) or {}
    driver = data.get('driver')
    pedido_id = data.get('pedido_id')
    contenido = data.get('contenido', '')
    
    if not driver or not contenido:
        return jsonify({'ok': False, 'error': 'driver y contenido requeridos'}), 400
    
    try:
        logger.info(f"🧾 Imprimiendo pedido #{pedido_id}")
        
        hprinter = win32print.OpenPrinter(driver)
        try:
            win32print.StartDocPrinter(hprinter, 1, (f"Pedido_{pedido_id}", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
            win32print.WritePrinter(hprinter, b'\n\n\n\n')
            win32print.WritePrinter(hprinter, b'\x1dV\x01')
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f"✅ Pedido #{pedido_id} impreso")
            return jsonify({
                'ok': True,
                'pedido_id': pedido_id
            })
        finally:
            win32print.ClosePrinter(hprinter)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'ok': False, 'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error: {e}")
    return jsonify({'ok': False, 'error': 'Error interno'}), 500

if __name__ == '__main__':
    logger.info(f"🖨️ PrintHost v{CONFIG['version']} iniciando...")
    
    # Registrarse en servidor central (opcional)
    code = register_to_registry()
    
    if code:
        logger.info(f"💾 Código: {code}")
        logger.info("⚠️ Guarda este código para configurar en PythonAnywhere")
    
    logger.info(f"📡 Escuchando en {CONFIG['host']}:{CONFIG['puerto']}")
    app.run(host=CONFIG['host'], port=CONFIG['puerto'], debug=False, use_reloader=False)
```

---

### PASO 3: Actualizar Cliente HTTP en Flask

Modificar `utils/print_client.py`:

```python
"""
Cliente HTTP PrintHost - Versión 2.1 con soporte para Registro Central
"""

import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PrintHostClient:
    def __init__(self, 
                 printhost_url: str = None,
                 client_code: str = None,
                 registry_url: str = None,
                 timeout: int = 10):
        """
        Inicializa cliente PrintHost
        
        Dos modos:
        1. Directo: printhost_url = "http://192.168.1.50:8765"
        2. Mediante registro: client_code = "ABC-123", registry_url = "http://..."
        """
        self.printhost_url = printhost_url
        self.client_code = client_code
        self.registry_url = registry_url
        self.timeout = timeout
        self._cached_url = None
    
    def _resolve_url(self) -> Optional[str]:
        """Resuelve URL del PrintHost (directo o via registro)"""
        if self.printhost_url:
            return self.printhost_url.rstrip('/')
        
        if self.client_code and self.registry_url:
            try:
                resp = requests.get(
                    f"{self.registry_url}/api/find-client/{self.client_code}",
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('ok'):
                        url = data.get('url', '').rstrip('/')
                        self._cached_url = url
                        logger.info(f"✅ PrintHost resuelto: {url}")
                        return url
            except Exception as e:
                logger.warning(f"Fallo en registro: {e}")
        
        return None
    
    def health_check(self) -> bool:
        """Verifica disponibilidad"""
        url = self._resolve_url()
        if not url:
            return False
        
        try:
            resp = requests.get(f"{url}/health", timeout=self.timeout)
            return resp.status_code == 200
        except:
            return False
    
    def list_printers(self) -> list:
        """Lista impresoras disponibles"""
        url = self._resolve_url()
        if not url:
            return []
        
        try:
            resp = requests.get(f"{url}/printers", timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json().get('printers', [])
        except Exception as e:
            logger.error(f"Error: {e}")
        
        return []
    
    def print_raw(self, 
                  driver: str,
                  content: str,
                  feed: int = 3,
                  cut: bool = True) -> Dict[str, Any]:
        """Imprime contenido RAW"""
        url = self._resolve_url()
        if not url:
            return {'ok': False, 'error': 'PrintHost no disponible'}
        
        try:
            payload = {
                'driver': driver,
                'content': content,
                'feed': feed,
                'cut': cut
            }
            
            resp = requests.post(
                f"{url}/print/raw",
                json=payload,
                timeout=self.timeout
            )
            
            return resp.json() if resp.status_code == 200 else \
                   {'ok': False, 'error': f'Status {resp.status_code}'}
        
        except requests.exceptions.ConnectionError:
            logger.error(f"No se puede conectar a PrintHost")
            return {'ok': False, 'error': 'PrintHost no disponible'}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {'ok': False, 'error': str(e)}
    
    def print_pedido(self,
                     driver: str,
                     pedido_id: int,
                     contenido: str) -> Dict[str, Any]:
        """Imprime un pedido"""
        url = self._resolve_url()
        if not url:
            return {'ok': False, 'error': 'PrintHost no disponible'}
        
        try:
            payload = {
                'driver': driver,
                'pedido_id': pedido_id,
                'contenido': contenido
            }
            
            resp = requests.post(
                f"{url}/print/pedido",
                json=payload,
                timeout=self.timeout
            )
            
            return resp.json() if resp.status_code == 200 else \
                   {'ok': False, 'error': f'Status {resp.status_code}'}
        
        except Exception as e:
            logger.error(f"Error pedido #{pedido_id}: {e}")
            return {'ok': False, 'error': str(e)}


def get_printhost_client(app=None) -> PrintHostClient:
    """Obtiene cliente PrintHost (directo o via registro)"""
    if app is None:
        from flask import current_app
        app = current_app
    
    # Opción 1: URL directa (para red local)
    printhost_url = app.config.get('PRINTHOST_URL')
    if printhost_url:
        return PrintHostClient(printhost_url=printhost_url)
    
    # Opción 2: Via registro (para redes diferentes)
    client_code = app.config.get('PRINTHOST_CODE')
    registry_url = app.config.get('REGISTRY_URL')
    if client_code and registry_url:
        return PrintHostClient(
            client_code=client_code,
            registry_url=registry_url
        )
    
    # Fallback
    return PrintHostClient(printhost_url='http://localhost:8765')
```

---

### PASO 4: Actualizar config.py

```python
class ProductionConfig():
    # ... otras configuraciones ...
    
    # Opción A: PrintHost directo (red local)
    PRINTHOST_URL = os.environ.get('PRINTHOST_URL', None)
    
    # Opción B: PrintHost via registro (diferente red)
    PRINTHOST_CODE = os.environ.get('PRINTHOST_CODE', None)  # Ej: "ABC-123"
    REGISTRY_URL = os.environ.get('REGISTRY_URL', None)      # Ej: "http://tu-server.com"
    
    PRINTER_NAME = os.environ.get('PRINTER_NAME', 'EPSON TM-T88V Receipt5')
```

---

### PASO 5: Configurar en WSGI de PythonAnywhere

```python
# Opción B: Usar registro central
os.environ['REGISTRY_URL'] = 'http://tu-servidor-registry.com'  # Donde corre printhost_registry.py
os.environ['PRINTHOST_CODE'] = 'ABC-123'  # Código que recibió el cliente al registrarse

# O Opción A: URL directa (si está en misma red)
os.environ['PRINTHOST_URL'] = 'http://192.168.1.50:8765'
```

---

## 🚀 FLUJO DE IMPLEMENTACIÓN

### En Cliente Windows:

1. Instalar `MundoWaffles_PrintHost.exe` v2.1
2. Ejecutar → Se registra automáticamente
3. Ver código generado → `ABC-123` (guardar)

### En PythonAnywhere:

1. Configurar variables en WSGI:
   ```python
   os.environ['REGISTRY_URL'] = 'http://tu-server-registry.com'
   os.environ['PRINTHOST_CODE'] = 'ABC-123'
   ```
2. Reload
3. Prueba: Crear pedido → Debe imprimir en cliente

---

## ✅ VENTAJAS DE OPCIÓN B

✅ Funciona **desde cualquier red** (diferentes ciudades)  
✅ No necesita configuración de IP/DNS  
✅ Cliente se registra automáticamente  
✅ Escalable a múltiples clientes  
✅ Código único por cliente  

🎉 **¡Impresión remota verdaderamente distribuida!**
