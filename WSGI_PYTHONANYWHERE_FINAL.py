# +++++++++++ FLASK - Mundo Waffles PythonAnywhere WSGI +++++++++++
# Este archivo debe reemplazar el contenido COMPLETO de:
# /var/www/josephmercury10_pythonanywhere_com_wsgi.py
#
# Dashboard PA → Web → Code → WSGI configuration file
# 1. Copiar TODO este contenido
# 2. Cambiar los 3 valores marcados con ← CAMBIAR
# 3. Save
# 4. Reload

import sys
import os

# ========== CONFIGURACIÓN DE RUTAS ==========
USERNAME = 'josephmercury10'  # Tu username de PythonAnywhere
PROJECT_DIR = 'mysite'         # Carpeta donde está tu proyecto

# Rutas absolutas
project_home = f'/home/{USERNAME}/{PROJECT_DIR}'
venv_path = f'/home/{USERNAME}/{PROJECT_DIR}/venv'

# ========== AGREGAR PROYECTO AL PATH ==========
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ========== ACTIVAR VIRTUAL ENVIRONMENT ==========
activate_this = os.path.join(venv_path, 'bin/activate_this.py')

# Verificar si existe activate_this.py
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))
else:
    # Alternativa si activate_this.py no existe (algunas versiones de virtualenv)
    import site
    site.addsitedir(os.path.join(venv_path, 'lib', 'python3.10', 'site-packages'))

# ========== VARIABLES DE ENTORNO ==========
# CRÍTICO: PythonAnywhere NO tiene panel de variables de entorno
# Las variables DEBEN configurarse aquí

# Forzar modo producción
os.environ['APP_ENV'] = 'production'

# Credenciales MySQL de PythonAnywhere
os.environ['PA_DB_HOST'] = 'josephmercury10.mysql.pythonanywhere-services.com'
os.environ['PA_DB_USER'] = 'josephmercury10'

# ⚠️ CAMBIAR ESTOS 3 VALORES:

# 1. Password de MySQL (Dashboard → Databases)
os.environ['PA_DB_PASSWORD'] = 'TU_PASSWORD_MYSQL_AQUI'  # ← CAMBIAR

# 2. Nombre de base de datos (Dashboard → Databases, incluir prefijo josephmercury10$)
# Si tu BD se llama "mundowaffles" → usar "josephmercury10$mundowaffles"
# Si tu BD se llama "dbmundo" → usar "josephmercury10$dbmundo"
os.environ['PA_DB_NAME'] = 'josephmercury10$mundowaffles'  # ← VERIFICAR Y CAMBIAR

# 3. Secret Key para Flask (generar con: python3 -c "import secrets; print(secrets.token_hex(32))")
# Ejemplo: a7f3b9e2c8d1f4a6b3e7c5d8f1a4b7e9c2f5a8d1b4e7c0f3a6b9d2e5f8a1b4c
os.environ['SECRET_KEY'] = 'PEGAR_RESULTADO_DE_SECRETS_TOKEN_HEX_AQUI'  # ← CAMBIAR

# ========== CONFIGURACIÓN DE PRINTHOST (OPCIONAL) ==========
# Si el cliente tiene PrintHost instalado en su PC para imprimir
# Configurar la IP del cliente donde está corriendo PrintHost.exe
# Ejemplo: os.environ['PRINTHOST_URL'] = 'http://192.168.1.50:8765'
# Si no usas impresoras, comentar o dejar como None
os.environ['PRINTHOST_URL'] = None  # ← CAMBIAR si usas impresora

# Nombre de impresora (debe coincidir con el nombre en PrintHost del cliente)
os.environ['PRINTER_NAME'] = 'EPSON TM-T88V Receipt5'  # ← CAMBIAR según tu impresora

# ========== IMPORTAR APLICACIÓN FLASK ==========
from app import app as application

# ========== CONFIGURACIÓN ADICIONAL (OPCIONAL) ==========
# Descomentar si necesitas limitar tamaño de uploads
# application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite 16MB
