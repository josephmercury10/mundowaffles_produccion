from flask import Flask, render_template, jsonify, redirect, url_for
import os
import platform
from config import config
from utils.db import db
from utils.filters import register_filters

# Importar los blueprints
from routes.marcas import marcas_bp
from routes.caracteristicas import caracteristicas_bp
from routes.categorias import categorias_bp
from routes.presentaciones import presentaciones_bp
from routes.productos import productos_bp
from routes.pos import pos_bp
from routes.clientes import clientes_bp
from routes.ventas import ventas_bp
from routes.pruebas import pruebas_bp
from routes.delivery import delivery_bp
from routes.printers import printers_bp
from routes.mostrador import mostrador_bp
from routes.api_print import api_print_bp
from routes.atributos import atributos_bp
from routes.reportes import reportes_bp


app = Flask(__name__)

# DETECCIÓN AUTOMÁTICA DE ENTORNO
# 1. Si APP_ENV está configurada, usarla
# 2. Si PA_DB_HOST está definida (producción), forzar 'production'
# 3. Por defecto, 'development'
ENV_NAME = os.environ.get('APP_ENV', None)

if not ENV_NAME:
    # Si PA_DB_HOST existe, es producción (PythonAnywhere)
    if os.environ.get('PA_DB_HOST'):
        ENV_NAME = 'production'
    else:
        ENV_NAME = os.environ.get('FLASK_ENV', 'development')

ENV_NAME = ENV_NAME.lower()

print(f"[FLASK] Entorno detectado: {ENV_NAME}", flush=True)

app.config.from_object(config.get(ENV_NAME, config['development']))

# CRÍTICO: En producción, construir SQLALCHEMY_DATABASE_URI dinámicamente
# para evitar socket Unix y usar conexión remota a MySQL en PythonAnywhere
if ENV_NAME == 'production':
    db_host = os.environ.get('PA_DB_HOST', 'josephmercury10.mysql.pythonanywhere-services.com')
    db_user = os.environ.get('PA_DB_USER', 'josephmercury10')
    db_pass = os.environ.get('PA_DB_PASSWORD', '')
    db_name = os.environ.get('PA_DB_NAME', 'josephmercury10$dbmundo')
    
    print(f"[FLASK] Configurando URI remota: mysql+pymysql://{db_user}:***@{db_host}/{db_name}", flush=True)
    
    # Usar mysql+pymysql para evitar socket Unix (funciona en Linux remoto)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"

# Inicializar bases de datos
# En desarrollo: usar Flask-MySQLdb (local) adem�s de SQLAlchemy
# En producci�n (PA): solo SQLAlchemy (MySQL remoto)
if ENV_NAME == 'development':
    from flask_mysqldb import MySQL
    conexion = MySQL(app)

# SQLAlchemy funciona en ambos entornos
db.init_app(app)

register_filters(app)


# Registrar los blueprints
app.register_blueprint(marcas_bp)
app.register_blueprint(caracteristicas_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(presentaciones_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(pos_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(pruebas_bp)
app.register_blueprint(delivery_bp)
app.register_blueprint(atributos_bp)
app.register_blueprint(reportes_bp)

# Registrar blueprints de impresoras (ahora funciona en ambas plataformas)
# - Windows: usa win32print directo
# - Linux: usa PrintHost (HTTP)
app.register_blueprint(printers_bp)
app.register_blueprint(mostrador_bp)
app.register_blueprint(api_print_bp)

# Ruta ra�z - redirige a mostrador
@app.route('/')
def index():
    return redirect(url_for('mostrador.index'))

#def pagina_no_encontrada(error):
 #   return "<h1>P�gina no encontrada</h1><p>Lo sentimos, la p�gina que buscas no existe.</p>"



if __name__ == '__main__':
    app.config.from_object(config.get(ENV_NAME, config['development']))
    #app.register_error_handler(404, pagina_no_encontrada)
    app.run()
