# 🎯 Despliegue Mundo Waffles en PythonAnywhere - Guía Completa

## 📌 TUS ERRORES ACTUALES Y SOLUCIÓN

### Error 1: `NameError: name 'redirect' is not defined`
- **Causa**: Archivo `app.py` desactualizado en servidor
- **Solución**: Subir `app.py` actualizado (primera línea debe tener todos los imports)

### Error 2: `ModuleNotFoundError: No module named 'flask_mysqldb'`
- **Causa**: Módulo no instalado en virtualenv de PA
- **Solución**: `pip install Flask-MySQLdb mysqlclient` en el venv

### Error 3: `ModuleNotFoundError: No module named 'win32print'` ⚡ NUEVO
- **Causa**: `utils/printer.py` importa `win32print` (solo Windows) sin verificar plataforma
- **Solución**: Subir `utils/printer.py` y `utils/printer_manager.py` actualizados con imports condicionales
- **Ver**: `FIX_WIN32PRINT_ERROR.md` para detalles completos

---

## ⚡ SOLUCIÓN EN 5 PASOS (10 minutos)

### PASO 1: Instalar dependencias en PythonAnywhere

```bash
# Abrir Bash Console en dashboard de PA
cd ~/mysite
source venv/bin/activate
pip install Flask-MySQLdb mysqlclient
```

### PASO 2: Subir archivos actualizados

**Carpetas a subir** (si no están ya):
- `routes/` completa
- `src/` completa  
- `templates/` completa
- `static/` completa
- `utils/` completa
- `forms/` si existe

**Archivos críticos**:
- `app.py` ← **IMPORTANTE: verificar que línea 1 tenga todos los imports**
- `config.py` ← **IMPORTANTE: debe tener ProductionConfig**
- `utils/printer.py` ← **NUEVO: imports condicionales de win32print**
- `utils/printer_manager.py` ← **NUEVO: imports condicionales**
- `forms.py`
- `requirements_production.txt`

### PASO 3: Configurar variables de entorno

Dashboard → Web → tu app → **Environment variables** → Add:

| Variable | Valor |
|----------|-------|
| `APP_ENV` | `production` |
| `PA_DB_HOST` | `josephmercury10.mysql.pythonanywhere-services.com` |
| `PA_DB_USER` | `josephmercury10` |
| `PA_DB_PASSWORD` | Tu password de MySQL |
| `PA_DB_NAME` | `josephmercury10$dbmundo` ⚠️ Verificar nombre exacto |
| `SECRET_KEY` | Generar con: `python3 -c "import secrets; print(secrets.token_hex(32))"` |

⚠️ **IMPORTANTE**: Verifica el nombre exacto de tu BD en **Databases** (debe incluir el prefijo `josephmercury10$`)

### PASO 4: Configurar archivo WSGI

Dashboard → Web → Code → click en archivo WSGI

**Reemplazar TODO con**:

```python
import sys
import os

# Ajustar si tu carpeta no se llama 'mysite'
project_home = '/home/josephmercury10/mysite'
venv_path = '/home/josephmercury10/mysite/venv'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

activate_this = os.path.join(venv_path, 'bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), dict(__file__=activate_this))

from app import app as application
```

### PASO 5: Configurar static files y RELOAD

**Static files**:
- Dashboard → Web → Static files → Add:
  - URL: `/static/`
  - Directory: `/home/josephmercury10/mysite/static`

**RELOAD**:
- Click en botón verde **"Reload"** en la página Web

---

## ✅ VERIFICACIÓN POST-DESPLIEGUE

### 1. Visitar sitio
`https://josephmercury10.pythonanywhere.com`

### 2. Si hay errores, revisar logs
Dashboard → Web → Log files → **Error log**

### 3. Test en consola Bash
```bash
cd ~/mysite
source venv/bin/activate

# Test 1: Verificar módulos
python -c "import flask_mysqldb; print('OK')"

# Test 2: Importar app
export APP_ENV=production
python -c "from app import app; print('App cargada OK')"
```

---

## 📋 ARCHIVOS DE AYUDA INCLUIDOS

1. **`SOLUCION_RAPIDA.md`** - Pasos urgentes para solucionar errores actuales
2. **`DEPLOY_PYTHONANYWHERE.md`** - Guía detallada completa
3. **`FIX_ERRORS_PA.md`** - Troubleshooting específico
4. **`requirements_production.txt`** - Dependencias sin libs de Windows
5. **`wsgi_pythonanywhere.py`** - Template del archivo WSGI
6. **`test_pa_deployment.sh`** - Script de verificación
7. **`check_deployment.sh`** - Verificación completa

---

## 🔧 CONFIGURACIÓN APLICADA AL PROYECTO

### Cambios en `config.py`:
- ✅ Agregada clase `ProductionConfig`
- ✅ Variables de entorno para credenciales MySQL
- ✅ `PRINTER_NAME = None` en producción (sin impresión térmica)
- ✅ `DEBUG = False` en producción

### Cambios en `app.py`:
- ✅ Selección de config por variable `APP_ENV`
- ✅ Blueprints de impresora solo se registran en Windows
- ✅ Compatible con producción en Linux

### Archivos creados:
- ✅ `requirements_production.txt` - sin dependencias de Windows
- ✅ `wsgi_pythonanywhere.py` - template WSGI
- ✅ Documentación completa de despliegue

---

## 🚨 NOTAS IMPORTANTES

### Base de Datos
- El nombre DEBE incluir el prefijo: `josephmercury10$nombre`
- Verificar en dashboard → Databases el nombre exacto
- Las tablas deben existir (migrar desde local o usar Alembic)

### Impresión Térmica
- **Deshabilitada automáticamente** en producción
- Solo funciona en desarrollo local (Windows)
- Rutas `/printers` y `/api/print` no se registran en PA

### Límites de PythonAnywhere (Free tier)
- 512 MB RAM
- 1 web app
- CPU limitado
- Sin tareas programadas (requiere upgrade)

### Variables de Entorno
- Se configuran en dashboard, **NO en consola Bash**
- Solo están disponibles en el proceso WSGI
- No usar `.env` files, PA las inyecta automáticamente

---

## 📞 COMANDOS ÚTILES

### Ver logs en tiempo real:
```bash
tail -f /var/log/josephmercury10.pythonanywhere.com.error.log
```

### Ver últimas 50 líneas:
```bash
tail -50 /var/log/josephmercury10.pythonanywhere.com.error.log
```

### Reinstalar dependencias:
```bash
cd ~/mysite
source venv/bin/activate
pip install -r requirements_production.txt --upgrade
```

### Test de conexión a BD:
```bash
mysql -h josephmercury10.mysql.pythonanywhere-services.com \
      -u josephmercury10 \
      -p \
      josephmercury10\$dbmundo
```

---

## 🎓 DOCUMENTACIÓN OFICIAL

- [Flask en PythonAnywhere](https://help.pythonanywhere.com/pages/Flask/)
- [MySQL en PythonAnywhere](https://help.pythonanywhere.com/pages/UsingMySQL/)
- [Debugging Import Errors](https://help.pythonanywhere.com/pages/DebuggingImportError/)
- [Variables de Entorno](https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/)

---

## 🏆 SIGUIENTE PASO

Una vez funcionando en PythonAnywhere:

1. **Migrar datos** de local a PA (exportar/importar SQL)
2. **Subir imágenes** de productos a `static/uploads/images/`
3. **Configurar dominio personalizado** (requiere cuenta paga)
4. **Habilitar HTTPS** (ya viene por defecto en PA)
5. **Backup regular** de la base de datos

---

**¿Listo para desplegar?** Sigue los 5 pasos de arriba en orden. ¡Éxito! 🚀
