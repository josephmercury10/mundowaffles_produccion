# +++++++++++ FLASK - Mundo Waffles PythonAnywhere WSGI +++++++++++
# Este archivo debe reemplazar el contenido de:
# /var/www/josephmercury10_pythonanywhere_com_wsgi.py

import sys
import os

# ========== CONFIGURACIÓN DE RUTAS ==========
# IMPORTANTE: Cambia 'josephmercury10' por tu username de PythonAnywhere
# IMPORTANTE: Cambia 'mysite' si subiste el proyecto a otra carpeta

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
# Asegúrate de configurar estas variables en el dashboard de PythonAnywhere:
# Web → Environment variables
#
# Variables requeridas:
# - APP_ENV=production
# - PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
# - PA_DB_USER=josephmercury10
# - PA_DB_PASSWORD=<tu_password_mysql>
# - PA_DB_NAME=josephmercury10$dbmundo (o el nombre de tu BD)
# - SECRET_KEY=<genera_con: python3 -c "import secrets; print(secrets.token_hex(32))">

# PythonAnywhere inyecta automáticamente las variables del dashboard al entorno

# ========== IMPORTAR APLICACIÓN FLASK ==========
from app import app as application

# Opcional: Configuración adicional si es necesario
# application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite upload 16MB
