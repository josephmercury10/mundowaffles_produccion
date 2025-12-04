# 🚀 SOLUCIÓN INMEDIATA - Errores en PythonAnywhere

## ⚡ PASOS RÁPIDOS (10 minutos)

### 0️⃣ ERROR CRÍTICO: ModuleNotFoundError: win32print
**Si ves este error, PRIMERO haz esto:**

Sube archivos actualizados:
- `utils/printer.py` (tiene imports condicionales de win32print)
- `utils/printer_manager.py` (tiene imports condicionales)

Dashboard PA → **Files** → `/home/josephmercury10/mysite/utils/` → reemplaza ambos archivos

Luego continúa con los pasos de abajo ↓

---

### 1️⃣ Instalar Flask-MySQLdb (URGENTE)
```bash
# En consola Bash de PythonAnywhere
cd ~/mysite
source venv/bin/activate
pip install Flask-MySQLdb mysqlclient
```

**Verificar**:
```bash
python -c "import flask_mysqldb; print('✓ Flask-MySQLdb instalado')"
```

---

### 2️⃣ Subir archivos actualizados
En dashboard PA → **Files** → navega a `/home/josephmercury10/mysite/`

**Archivos CRÍTICOS a reemplazar**:

#### ✅ `app.py` 
Asegúrate que la línea 1 sea EXACTAMENTE:
```python
from flask import Flask, render_template, jsonify, redirect, url_for
```

#### ✅ `config.py`
Debe tener `ProductionConfig` con:
```python
MYSQL_HOST = os.environ.get('PA_DB_HOST', 'josephmercury10.mysql.pythonanywhere-services.com')
MYSQL_USER = os.environ.get('PA_DB_USER', 'josephmercury10')
MYSQL_PASSWORD = os.environ.get('PA_DB_PASSWORD', '')
MYSQL_DB = os.environ.get('PA_DB_NAME', 'josephmercury10$dbmundo')
```

**IMPORTANTE**: Sube los archivos actualizados de tu carpeta local.

---

### 3️⃣ Configurar Variables de Entorno
Dashboard PA → **Web** → tu app → **Environment variables**

Agregar estas 6 variables (click "Add a new environment variable"):

```
APP_ENV = production
PA_DB_HOST = josephmercury10.mysql.pythonanywhere-services.com
PA_DB_USER = josephmercury10
PA_DB_PASSWORD = (tu password de MySQL)
PA_DB_NAME = josephmercury10$dbmundo
SECRET_KEY = (generar con comando de abajo)
```

**Generar SECRET_KEY** (en Bash console):
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copia el output y úsalo como valor de `SECRET_KEY`.

---

### 4️⃣ Verificar nombre de Base de Datos
Dashboard PA → **Databases** → revisa el nombre EXACTO de tu base de datos.

En PythonAnywhere, las BDs tienen formato: `josephmercury10$nombre`

**Ejemplo**:
- Si creaste BD llamada `dbmundo` → el nombre real es `josephmercury10$dbmundo`
- Si creaste BD llamada `mundowaffles` → usar `josephmercury10$mundowaffles`

⚠️ Actualiza la variable `PA_DB_NAME` con el nombre EXACTO que ves en Databases.

---

### 5️⃣ Configurar archivo WSGI
Dashboard → **Web** → **Code** → click en tu archivo WSGI (algo como `/var/www/josephmercury10_pythonanywhere_com_wsgi.py`)

**Contenido completo del archivo**:

```python
import sys
import os

# Rutas del proyecto
project_home = '/home/josephmercury10/mysite'
venv_path = '/home/josephmercury10/mysite/venv'

# Agregar al path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activar virtualenv
activate_this = os.path.join(venv_path, 'bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

# Importar app
from app import app as application
```

---

### 6️⃣ Configurar Static Files
Dashboard → **Web** → **Static files** → Add new static file mapping:

```
URL: /static/
Directory: /home/josephmercury10/mysite/static
```

---

### 7️⃣ RELOAD
Dashboard → **Web** → Click botón verde **"Reload josephmercury10.pythonanywhere.com"**

---

## 🔍 VERIFICACIÓN

### Ver si funciona:
Visita: `https://josephmercury10.pythonanywhere.com`

### Si hay errores:
Dashboard → **Web** → **Log files** → **Error log**

---

## 🐛 ERRORES RESUELTOS

### ✅ Error 1: `NameError: name 'redirect' is not defined`
**Solución**: Paso 2️⃣ - Subir `app.py` actualizado con imports correctos

### ✅ Error 2: `ModuleNotFoundError: No module named 'flask_mysqldb'`
**Solución**: Paso 1️⃣ - Instalar Flask-MySQLdb en virtualenv

---

## 📋 CHECKLIST FINAL

Antes de hacer Reload, verifica:

- [ ] Flask-MySQLdb instalado (`pip list | grep Flask-MySQLdb`)
- [ ] `app.py` subido y tiene `from flask import ... redirect, url_for`
- [ ] `config.py` subido con `ProductionConfig`
- [ ] 6 variables de entorno configuradas
- [ ] Nombre de BD correcto con prefijo `josephmercury10$`
- [ ] Archivo WSGI configurado
- [ ] Static files mapeados
- [ ] Carpeta `static/` completa subida al servidor

---

## 🆘 SI AÚN HAY ERRORES

1. **Copia las últimas 30 líneas del error log**:
```bash
tail -30 /var/log/josephmercury10.pythonanywhere.com.error.log
```

2. **Verifica importación manual**:
```bash
cd ~/mysite
source venv/bin/activate
python -c "from app import app; print('OK')"
```

Si da error, copia el mensaje completo.

3. **Verifica variables de entorno** están cargadas en el proceso WSGI (no en Bash console)

---

## 📞 RECURSOS

- **Documentación PA Flask**: https://help.pythonanywhere.com/pages/Flask/
- **Debugging Import Errors**: https://help.pythonanywhere.com/pages/DebuggingImportError/
- **MySQL en PA**: https://help.pythonanywhere.com/pages/UsingMySQL/

---

**Tiempo estimado**: 5-10 minutos siguiendo los pasos en orden.
