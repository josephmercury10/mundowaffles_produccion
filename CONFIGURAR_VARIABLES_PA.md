# 🚀 CONFIGURACIÓN PYTHONANYWHERE - ARCHIVO WSGI

## ⚠️ IMPORTANTE: PythonAnywhere NO tiene panel de variables de entorno

A diferencia de Heroku/Render/Railway, PythonAnywhere **NO tiene interfaz gráfica** para configurar variables de entorno.

**SOLUCIÓN**: Las variables se configuran **directamente en el archivo WSGI**.

---

## 📝 PASO 1: Abrir Archivo WSGI

### Ubicación
Dashboard PA → **Web** → Sección **Code** → Click en:

```
WSGI configuration file: /var/www/josephmercury10_pythonanywhere_com_wsgi.py
```

Se abrirá un editor web.

---

## 📋 PASO 2: Copiar Contenido del Template

**Archivo**: `WSGI_PYTHONANYWHERE_FINAL.py` (en tu proyecto local)

**Instrucciones:**
1. Abrir `WSGI_PYTHONANYWHERE_FINAL.py` en VS Code
2. **Copiar TODO el contenido** (Ctrl+A → Ctrl+C)
3. En el editor WSGI de PythonAnywhere: **Seleccionar todo y pegar** (reemplazar contenido actual)

---

## ⚙️ PASO 3: Configurar 3 Variables Críticas

Dentro del archivo WSGI, buscar esta sección:

```python
# ⚠️ CAMBIAR ESTOS 3 VALORES:

# 1. Password de MySQL (Dashboard → Databases)
os.environ['PA_DB_PASSWORD'] = 'TU_PASSWORD_MYSQL_AQUI'  # ← CAMBIAR

# 2. Nombre de BD (Dashboard → Databases, incluir prefijo josephmercury10$)
os.environ['PA_DB_NAME'] = 'josephmercury10$mundowaffles'  # ← CAMBIAR

# 3. Secret Key para Flask
os.environ['SECRET_KEY'] = 'PEGAR_RESULTADO_AQUI'  # ← CAMBIAR
```

---

## 🔑 PASO 3A: Obtener Password de MySQL

1. Dashboard PA → **Databases**
2. Buscar tu base de datos en la lista
3. Si olvidaste el password: Click **Reset password**
4. Copiar el password y pegar en `PA_DB_PASSWORD`

**Ejemplo:**
```python
os.environ['PA_DB_PASSWORD'] = 'MiPassword123!'  # ← Tu password real
```

---

## 🗄️ PASO 3B: Verificar Nombre de Base de Datos

1. Dashboard PA → **Databases**
2. Buscar tu BD en la lista (ej: `mundowaffles` o `dbmundo`)
3. **Nombre real incluye prefijo de usuario**: `josephmercury10$nombre_bd`

**Ejemplos:**
- Ves `mundowaffles` → Usar `josephmercury10$mundowaffles`
- Ves `dbmundo` → Usar `josephmercury10$dbmundo`

```python
os.environ['PA_DB_NAME'] = 'josephmercury10$mundowaffles'  # ← Verificar nombre
```

---

## 🔐 PASO 3C: Generar SECRET_KEY

### En Bash Console de PythonAnywhere:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Copiar resultado** (64 caracteres aleatorios):
```
a7f3b9e2c8d1f4a6b3e7c5d8f1a4b7e9c2f5a8d1b4e7c0f3a6b9d2e5f8a1b4c
```

**Pegar en WSGI:**
```python
os.environ['SECRET_KEY'] = 'a7f3b9e2c8d1f4a6b3e7c5d8f1a4b7e9c2f5a8d1b4e7c0f3a6b9d2e5f8a1b4c'
```

---

## 💾 PASO 4: Guardar Archivo WSGI

- Click **Save** en esquina superior derecha del editor

---

## 🔄 PASO 5: Reload Aplicación

1. Dashboard PA → **Web**
2. Click botón verde **Reload josephmercury10.pythonanywhere.com**
3. Esperar que aparezca ✅ "reloaded"

---

## 🧪 PASO 6: Verificar Error Log

Dashboard PA → **Web** → **Log files** → Click:
```
Error log: /var/log/josephmercury10.pythonanywhere.com.error.log
```

### ✅ Si todo está bien:
```
[FLASK] Entorno detectado: production
[FLASK] Configurando URI remota: mysql+pymysql://josephmercury10:***@...
```

### ❌ Si hay errores comunes:

**Error: "Can't connect to socket"**
```
→ Verificar que os.environ['APP_ENV'] = 'production' esté en WSGI
→ Verificar que os.environ['PA_DB_HOST'] esté configurado
→ Hacer Reload de nuevo
```

**Error: "Access denied for user 'josephmercury10'"**
```
→ Password incorrecto en PA_DB_PASSWORD
→ Dashboard → Databases → Reset password
```

**Error: "Unknown database 'mundowaffles'"**
```
→ Falta prefijo en PA_DB_NAME
→ Debe ser: josephmercury10$mundowaffles (con prefijo)
```

**Error: "Unknown database 'josephmercury10'"**
```
→ Nombre de BD incorrecto o BD no existe
→ Verificar nombre exacto en Dashboard → Databases
```

**Error: "SyntaxError" en config.py o app.py**
```
→ Archivos no subidos correctamente a PA
→ Resubir app.py y config.py desde local
```

---

## 🎯 EJEMPLO COMPLETO DE ARCHIVO WSGI

```python
import sys
import os

# Rutas
project_home = '/home/josephmercury10/mysite'
venv_path = '/home/josephmercury10/mysite/venv'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activar virtualenv
activate_this = os.path.join(venv_path, 'bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

# ========== VARIABLES DE ENTORNO ==========
os.environ['APP_ENV'] = 'production'
os.environ['PA_DB_HOST'] = 'josephmercury10.mysql.pythonanywhere-services.com'
os.environ['PA_DB_USER'] = 'josephmercury10'
os.environ['PA_DB_PASSWORD'] = 'MiPassword123!'  # ← TU PASSWORD
os.environ['PA_DB_NAME'] = 'josephmercury10$mundowaffles'  # ← TU BD
os.environ['SECRET_KEY'] = 'a7f3b9e2c8d1f4a6b3e7c5d8f1a4b7e9c2f5a8d1b4e7c0f3a6b9d2e5f8a1b4c'

# Importar app
from app import app as application
```

---

## 🔍 VERIFICAR CONFIGURACIÓN EN PA

### Opción 1: Error Log (Más Rápido)

Dashboard PA → Web → Error log → Ver últimas líneas

**Buscar líneas como:**
```
[FLASK] Entorno detectado: production
[FLASK] Configurando URI remota: mysql+pymysql://josephmercury10:***@...
```

### Opción 2: Bash Console (Test Manual)

```bash
cd ~/mysite
source venv/bin/activate

python << 'EOF'
import os
print("=== VARIABLES CONFIGURADAS ===")
print(f"APP_ENV: {os.environ.get('APP_ENV', 'NO SET')}")
print(f"PA_DB_HOST: {os.environ.get('PA_DB_HOST', 'NO SET')}")
print(f"PA_DB_USER: {os.environ.get('PA_DB_USER', 'NO SET')}")
print(f"PA_DB_PASSWORD: {'***' if os.environ.get('PA_DB_PASSWORD') else 'NO SET'}")
print(f"PA_DB_NAME: {os.environ.get('PA_DB_NAME', 'NO SET')}")
print(f"SECRET_KEY: {'***' if os.environ.get('SECRET_KEY') else 'NO SET'}")

print("\n=== PROBANDO IMPORTACIÓN ===")
try:
    from app import app
    print("✅ app.py importado sin errores")
    
    with app.app_context():
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NO SET')
        print(f"\n=== CONFIGURACIÓN FLASK ===")
        print(f"URI: {uri[:60]}..." if len(str(uri)) > 60 else f"URI: {uri}")
        print(f"DEBUG: {app.config.get('DEBUG')}")
        
        from utils.db import db
        db.session.execute("SELECT 1")
        print("\n✅ CONEXIÓN A BD EXITOSA")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)[:200]}")
EOF
```

**Salida esperada:**
```
=== VARIABLES CONFIGURADAS ===
APP_ENV: production
PA_DB_HOST: josephmercury10.mysql.pythonanywhere-services.com
PA_DB_USER: josephmercury10
PA_DB_PASSWORD: ***
PA_DB_NAME: josephmercury10$mundowaffles
SECRET_KEY: ***

=== PROBANDO IMPORTACIÓN ===
✅ app.py importado sin errores

=== CONFIGURACIÓN FLASK ===
URI: mysql+pymysql://josephmercury10:***@josephmercury10.mysql...
DEBUG: False

✅ CONEXIÓN A BD EXITOSA
```

---

## 📋 CHECKLIST COMPLETO

### Archivo WSGI en PythonAnywhere:

- [ ] ✅ Copiado template completo de `WSGI_PYTHONANYWHERE_FINAL.py`
- [ ] ✅ `os.environ['APP_ENV'] = 'production'`
- [ ] ✅ `os.environ['PA_DB_HOST'] = 'josephmercury10.mysql.pythonanywhere-services.com'`
- [ ] ✅ `os.environ['PA_DB_USER'] = 'josephmercury10'`
- [ ] ✅ `os.environ['PA_DB_PASSWORD']` con password real de MySQL
- [ ] ✅ `os.environ['PA_DB_NAME']` con prefijo `josephmercury10$` y nombre correcto
- [ ] ✅ `os.environ['SECRET_KEY']` con clave generada por `secrets.token_hex(32)`
- [ ] ✅ Última línea: `from app import app as application`
- [ ] ✅ Archivo guardado (Save)

### En Dashboard PA:

- [ ] ✅ Reload ejecutado (botón verde)
- [ ] ✅ Error log revisado (sin errores de socket o sintaxis)
- [ ] ✅ Sitio accesible: https://josephmercury10.pythonanywhere.com

### Archivos subidos a PA:

- [ ] ✅ `app.py` (con auto-detección de entorno)
- [ ] ✅ `config.py` (sin errores de sintaxis)
- [ ] ✅ `utils/printer.py` y `utils/printer_manager.py` (imports condicionales)
- [ ] ✅ `pymysql` instalado: `pip install pymysql`

---

## 🆘 TROUBLESHOOTING

### ❌ Error: "SyntaxError: unmatched '}'"

**Causa**: Archivo `config.py` o `app.py` tiene error de sintaxis

**Solución**:
1. Verificar que `config.py` en PA coincida con versión local
2. Resubir archivos desde local a PA
3. Verificar codificación UTF-8 (sin caracteres raros)

### ❌ Error: "Can't connect to socket"

**Causa**: Variables de entorno no configuradas en WSGI

**Solución**:
1. Verificar que WSGI tenga todas las líneas `os.environ[...]`
2. Verificar que `APP_ENV = 'production'`
3. Reload después de cambiar WSGI

### ❌ Error: "Access denied for user"

**Causa**: Password incorrecto

**Solución**:
1. Dashboard → Databases → Reset password
2. Actualizar `PA_DB_PASSWORD` en WSGI
3. Save y Reload

### ❌ Error: "Unknown database"

**Causa**: Nombre de BD sin prefijo o incorrecto

**Solución**:
1. Dashboard → Databases → Ver nombre exacto
2. Agregar prefijo: `josephmercury10$nombre_bd`
3. Actualizar `PA_DB_NAME` en WSGI

---

## 🔐 SEGURIDAD

⚠️ **El archivo WSGI NO es público en PythonAnywhere**, pero:
- **NO** subir archivo WSGI a GitHub
- **NO** compartir screenshots con credenciales
- Cambiar `SECRET_KEY` periódicamente
- Usar passwords fuertes para MySQL

---

## ✅ RESUMEN EJECUTIVO

**PythonAnywhere NO tiene panel de variables de entorno.**

**Configuración en 5 pasos:**

1. **Copiar** `WSGI_PYTHONANYWHERE_FINAL.py` al editor WSGI de PA
2. **Cambiar 3 valores**: `PA_DB_PASSWORD`, `PA_DB_NAME`, `SECRET_KEY`
3. **Save** archivo WSGI
4. **Reload** aplicación
5. **Verificar** error log (sin errores de socket)

🎉 **Una vez configurado, el error de socket MySQL desaparecerá.**
