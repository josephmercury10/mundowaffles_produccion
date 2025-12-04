# Guía de Despliegue en PythonAnywhere

## 1. Preparar Archivos Locales

### Crear requirements.txt sin dependencias de Windows
Las siguientes librerías son **solo para Windows** y deben excluirse en producción:
- `pywin32==311` (Windows Print Spooler)
- `waitress==3.0.2` (servidor Windows, PA usa Gunicorn/uWSGI)
- `python-escpos==3.1` (puede tener dependencias USB/serial de Windows)
- `pyserial==3.5` (serial ports, no aplica en PA)
- `pyusb==1.3.1` (USB devices, no aplica en PA)

Crea `requirements_production.txt`:
```bash
alembic==1.16.5
blinker==1.9.0
click==8.2.1
Flask==3.1.2
Flask-Login==0.6.3
Flask-MySQLdb==2.0.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
greenlet==3.2.4
itsdangerous==2.2.0
Jinja2==3.1.6
Mako==1.3.10
MarkupSafe==3.0.2
mysqlclient==2.2.7
pillow==12.0.0
python-barcode==0.16.1
qrcode==8.2
six==1.17.0
SQLAlchemy==2.0.43
typing_extensions==4.14.1
Werkzeug==3.1.3
WTForms==3.2.1
```

## 2. Subir Código a PythonAnywhere

### Opción A: Git (Recomendado)
```bash
# En consola Bash de PythonAnywhere
cd ~
git clone <tu_repositorio> mysite
cd mysite
```

### Opción B: Upload Manual
1. Ve a **Files** en dashboard de PA
2. Sube carpetas: `routes/`, `src/`, `templates/`, `static/`, `utils/`, `forms/`
3. Sube archivos: `app.py`, `config.py`, `forms.py`, `requirements_production.txt`

## 3. Configurar Base de Datos

Ya tienes la BD creada con:
- **Host**: `josephmercury10.mysql.pythonanywhere-services.com`
- **Usuario**: `josephmercury10`
- **Base de datos**: `josephmercury10$dbmundo` (o el nombre que hayas creado)

Verifica el nombre exacto en **Databases** → tu base aparecerá como `josephmercury10$<nombre>`

## 4. Crear y Configurar Virtual Environment

```bash
# En consola Bash de PythonAnywhere
cd ~/mysite
python3.10 -m venv venv  # o python3.11/3.12 según disponibilidad
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_production.txt
```

**Importante**: Si `mysqlclient` falla al instalarse, instala primero las dependencias del sistema:
```bash
# Contacta soporte de PA si necesitas: libmysqlclient-dev, python3-dev
# Normalmente ya están disponibles
```

## 5. Configurar Variables de Entorno

En el dashboard de PythonAnywhere, ve a **Web** → tu app → sección **Environment variables**:

| Variable | Valor |
|----------|-------|
| `APP_ENV` | `production` |
| `PA_DB_HOST` | `josephmercury10.mysql.pythonanywhere-services.com` |
| `PA_DB_USER` | `josephmercury10` |
| `PA_DB_PASSWORD` | `<tu_password_mysql>` |
| `PA_DB_NAME` | `josephmercury10$dbmundo` |
| `SECRET_KEY` | `<genera_clave_aleatoria_larga>` |

**Generar SECRET_KEY** (en consola Bash de PA):
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 6. Configurar WSGI File

En **Web** → **Code** → click en el link del archivo WSGI (ej: `/var/www/josephmercury10_pythonanywhere_com_wsgi.py`)

**Reemplaza TODO el contenido** con:

```python
# +++++++++++ FLASK +++++++++++
import sys
import os

# Agregar directorio del proyecto
project_home = '/home/josephmercury10/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activar virtualenv
activate_this = os.path.join('/home/josephmercury10/mysite/venv/bin/activate_this.py')
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Cargar variables de entorno desde el dashboard de PA
# (PA las inyecta automáticamente)

# Importar aplicación Flask
from app import app as application
```

**Ajusta rutas** si tu estructura es diferente:
- Cambia `josephmercury10` por tu username de PA
- Cambia `mysite` si subiste a otra carpeta

## 7. Configurar Static Files

En **Web** → **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/josephmercury10/mysite/static` |

## 8. Migrar Base de Datos (Opcional)

Si necesitas ejecutar migraciones de Alembic:

```bash
cd ~/mysite
source venv/bin/activate
export APP_ENV=production
export PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
export PA_DB_USER=josephmercury10
export PA_DB_PASSWORD=<tu_password>
export PA_DB_NAME=josephmercury10$dbmundo
export SECRET_KEY=<tu_secret_key>

# Ejecutar migraciones
alembic upgrade head
```

**Nota**: Si la BD ya tiene las tablas creadas, omite este paso.

## 9. Reload y Probar

1. Click en **Reload** (botón verde en la página de tu web app)
2. Visita `https://josephmercury10.pythonanywhere.com`
3. Verifica logs en **Error log** si hay problemas

## 10. Verificación de Errores Comunes

### Error: `ModuleNotFoundError: No module named 'flask_mysqldb'`
**Solución**:
```bash
source ~/mysite/venv/bin/activate
pip install Flask-MySQLdb mysqlclient
```

### Error: `NameError: name 'redirect' is not defined`
**Causa**: Versión vieja de `app.py` en servidor  
**Solución**: Vuelve a subir `app.py` actualizado (asegúrate línea 1 tiene todos los imports)

### Error: Conexión a BD fallida
**Solución**: Verifica que:
- Variables de entorno estén configuradas correctamente
- Nombre de BD sea `josephmercury10$<nombre>` (con el prefijo del usuario)
- Password de MySQL sea correcto

### Error: `ImportError` en rutas o modelos
**Solución**: Asegúrate de subir TODAS las carpetas:
```bash
# Verificar en consola Bash de PA
ls ~/mysite/
# Debe listar: app.py, routes/, src/, templates/, static/, utils/, forms/
```

## 11. Configuración de Producción

### Deshabilitar Debug
Ya está configurado en `ProductionConfig` con `DEBUG=False`

### Logs de Aplicación
- **Error log**: Dashboard → Web → Log files → Error log
- **Server log**: Dashboard → Web → Log files → Server log

### Uploads de Imágenes
Asegúrate de que las carpetas existan:
```bash
mkdir -p ~/mysite/static/uploads/images
mkdir -p ~/mysite/static/uploads/files
chmod 755 ~/mysite/static/uploads
```

## 12. Mantenimiento

### Actualizar Código
```bash
cd ~/mysite
git pull  # si usas Git
# o sube archivos manualmente
```
Luego: **Reload** en dashboard

### Ver Logs en Tiempo Real
```bash
tail -f /var/log/josephmercury10.pythonanywhere.com.error.log
```

### Reinstalar Dependencias
```bash
source ~/mysite/venv/bin/activate
pip install -r requirements_production.txt --upgrade
```

## Notas Importantes

1. **Impresión Térmica**: Deshabilitada automáticamente en PA (solo funciona en Windows local)
2. **Blueprints de Printer**: No se registran en producción (verificar con `APP_ENV=production`)
3. **Archivos Estáticos**: Servidos por nginx de PA, no por Flask
4. **Zona Horaria**: PA usa UTC por defecto, ajusta en modelos si es necesario
5. **Límites Free Tier**: 
   - 512 MB RAM
   - 1 web app
   - CPU limitado
   - Considera upgrade si tienes muchas visitas concurrentes

## Soporte

- Documentación PA: https://help.pythonanywhere.com/
- Foro: https://www.pythonanywhere.com/forums/
- Error logs en dashboard son tu mejor amigo
