from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Agregar el directorio raíz al path para importar modelos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar db y todos los modelos
from utils.db import db

# Importar configuraciones del proyecto
from config import config as app_config

# Importar todos los modelos para que SQLAlchemy los detecte
from src.models.Venta_model import TipoVenta, ProductoVenta, Venta
from src.models.Producto_model import Producto
from src.models.Categoria_model import Categoria
from src.models.Marca_model import Marca
from src.models.Presentacion_model import Presentacion
from src.models.Caracteristica_model import Caracteristica
from src.models.AtributoProducto_model import AtributoProducto
from src.models.ValorAtributo_model import ValorAtributo
from src.models.Cliente_model import Cliente
from src.models.Persona_model import Persona
from src.models.Documento_model import Documento
from src.models.Comprobante_model import Comprobante
from src.models.MetodoPago_model import MetodoPago
from src.models.User_model import User
from src.models.Printer_model import Printer
from src.models.repartidores_model import Repartidor
from src.models.Compra_model import Compra

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Detectar ambiente automáticamente
# Prioridad: 1) FLASK_ENV, 2) Detección de PythonAnywhere, 3) localhost por defecto
def detectar_ambiente():
    """Detecta si estamos en producción (PythonAnywhere) o desarrollo (localhost)"""
    
    # 1. Si FLASK_ENV está definido, usarlo
    flask_env = os.environ.get('FLASK_ENV')
    if flask_env:
        return flask_env
    
    # 2. Detectar PythonAnywhere: verificar si existe variable PA_DB_HOST o USER contiene pythonanywhere
    if os.environ.get('PA_DB_HOST') or 'pythonanywhere' in os.environ.get('USER', '').lower():
        return 'production'
    
    # 3. Por defecto: desarrollo
    return 'development'

environment = detectar_ambiente()
config_class = app_config.get(environment, app_config['development'])

# Construir la URI según el ambiente
if environment == 'production':
    # PythonAnywhere: construir desde variables de entorno
    db_host = os.environ.get('PA_DB_HOST', 'josephmercury10.mysql.pythonanywhere-services.com')
    db_user = os.environ.get('PA_DB_USER', 'josephmercury10')
    db_pass = os.environ.get('PA_DB_PASSWORD', '')
    db_name = os.environ.get('PA_DB_NAME', 'josephmercury10$mundowaffles')
    sqlalchemy_url = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    print(f"🔧 Alembic [PRODUCCIÓN]: Conectando a {db_host}/{db_name}")
else:
    # Desarrollo: localhost
    sqlalchemy_url = 'mysql+pymysql://root:@localhost:3309/dbmundo'
    print(f"🔧 Alembic [DESARROLLO]: Conectando a localhost:3309/dbmundo")

# Override de la URL de SQLAlchemy en alembic.ini
config.set_main_option('sqlalchemy.url', sqlalchemy_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
