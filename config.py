import os


class DevelopmentConfig():
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost:3309/dbmundo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'dbmundo'
    SECRET_KEY = os.environ.get('SECRET_KEY', '1234')
    UPLOADED_IMAGES_DEST = 'static/uploads/images'
    UPLOADED_FILES_DEST = 'static/uploads/files'
    # Impresora en desarrollo (Windows local)
    PRINTER_NAME = os.environ.get('PRINTER_NAME', 'EPSON TM-T88V Receipt5')
    # PrintHost no se usa en desarrollo (se usa win32print directo)
    PRINTHOST_URL = None


class ProductionConfig():
    # Credenciales para PythonAnywhere - leer de variables de entorno
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    UPLOADED_IMAGES_DEST = 'static/uploads/images'
    UPLOADED_FILES_DEST = 'static/uploads/files'
    # Nombre de impresora para PrintHost (cliente configura la suya)
    PRINTER_NAME = os.environ.get('PRINTER_NAME', 'EPSON TM-T88V Receipt5')
    
    # MySQL para Flask-MySQLdb (solo referencia, SQLAlchemy usa URI)
    MYSQL_HOST = os.environ.get('PA_DB_HOST', 'josephmercury10.mysql.pythonanywhere-services.com')
    MYSQL_USER = os.environ.get('PA_DB_USER', 'josephmercury10')
    MYSQL_PASSWORD = os.environ.get('PA_DB_PASSWORD', '')
    MYSQL_DB = os.environ.get('PA_DB_NAME', 'josephmercury10$mundowaffles')
    
    # Placeholder para URI (se construye en app.py después de cargar config)
    SQLALCHEMY_DATABASE_URI = None
    
    # PrintHost: Cliente debe configurar en WSGI (el servidor solo envía /print/job)
    # Ejemplo: os.environ['PRINTHOST_URL'] = 'http://192.168.1.50:8765'
    PRINTHOST_URL = os.environ.get('PRINTHOST_URL', None)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
