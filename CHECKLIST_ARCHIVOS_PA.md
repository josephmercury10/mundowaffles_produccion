# ✅ CHECKLIST FINAL - Archivos para PythonAnywhere

## 📦 ARCHIVOS QUE DEBES SUBIR

### 🔴 CRÍTICOS (sin estos la app no carga)

1. **`app.py`**
   - ✅ Imports: `from flask import Flask, render_template, jsonify, redirect, url_for`
   - ✅ Selección de config por `APP_ENV`
   - ✅ Blueprints de printer solo en Windows

2. **`config.py`**
   - ✅ `ProductionConfig` con variables de entorno
   - ✅ Credenciales MySQL de PythonAnywhere
   - ✅ `PRINTER_NAME = None` en producción

3. **`utils/printer.py`**
   - ✅ Import condicional de `win32print`
   - ✅ Detecta plataforma con `platform.system()`
   - ✅ No falla en Linux

4. **`utils/printer_manager.py`**
   - ✅ Import condicional de `win32print`
   - ✅ Funciones retornan vacío si no hay win32

5. **`templates/base.html`**
   - ✅ Enlace a printers solo si `config.PRINTER_NAME`
   - ✅ No genera BuildError en producción

---

### 🟡 IMPORTANTES (carpetas completas)

6. **`routes/`** - Todos los blueprints
   - `delivery.py`, `mostrador.py`, `ventas.py`, etc.

7. **`src/models/`** - Todos los modelos
   - `Producto_model.py`, `Venta_model.py`, `Cliente_model.py`, etc.

8. **`templates/`** - Todos los templates
   - Incluye subcarpetas: `ventas/`, `productos/`, etc.

9. **`static/`** - Archivos estáticos
   - `css/`, `js/`, `uploads/`

10. **`forms/` o `forms.py`** - Formularios WTForms

11. **`utils/`** - Utilities (ya incluiste printer.py y printer_manager.py)
    - `db.py`, `filters.py`, `helpers_db.py`

---

### 🟢 OPCIONALES (para referencia)

12. **`requirements_production.txt`** - Para instalar dependencias
13. **`wsgi_pythonanywhere.py`** - Template del archivo WSGI
14. **Documentación** - Los archivos `.md` creados

---

## 🎯 MÉTODO RÁPIDO: Subir todo el proyecto

### Opción A: Git (Recomendado)

```bash
# En tu máquina local
git init  # si no tienes repo
git add .
git commit -m "Configuración para PythonAnywhere"
git push origin main

# En PythonAnywhere Bash console
cd ~
git clone <tu_repo> mysite
```

### Opción B: Comprimir y subir

```powershell
# En tu máquina local (PowerShell)
# Excluir carpetas innecesarias
$exclude = @('env', '__pycache__', 'build', '.git', 'alembic')
Compress-Archive -Path * -DestinationPath mundowaffles.zip -Force
```

Luego en PA:
- Dashboard → Files → Upload
- Sube `mundowaffles.zip`
- En Bash console: `unzip mundowaffles.zip -d mysite`

### Opción C: Upload manual selectivo

Dashboard → Files → Upload one at a time (lento pero seguro)

---

## ⚙️ CONFIGURACIÓN EN PYTHONANYWHERE

### 1. Variables de Entorno
Dashboard → Web → Environment variables

```
APP_ENV=production
PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
PA_DB_USER=josephmercury10
PA_DB_PASSWORD=<tu_password_mysql>
PA_DB_NAME=josephmercury10$dbmundo
SECRET_KEY=<generar_con: python3 -c "import secrets; print(secrets.token_hex(32))">
```

### 2. Archivo WSGI
Dashboard → Web → Code → WSGI file

Copiar contenido de `wsgi_pythonanywhere.py`

### 3. Static Files
Dashboard → Web → Static files

```
URL: /static/
Directory: /home/josephmercury10/mysite/static
```

### 4. Virtual Environment
```bash
cd ~/mysite
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements_production.txt
```

### 5. Reload
Dashboard → Web → Reload button

---

## 🧪 VERIFICACIÓN PRE-RELOAD

```bash
cd ~/mysite
source venv/bin/activate

# 1. Verificar archivos críticos
echo "=== Verificando archivos ==="
ls -la app.py config.py
ls -la utils/printer.py utils/printer_manager.py
ls -la templates/base.html

# 2. Verificar primera línea de app.py
echo "=== Primera línea de app.py ==="
head -1 app.py
# Debe mostrar: from flask import Flask, render_template, jsonify, redirect, url_for

# 3. Test de imports
echo "=== Test de imports ==="
export APP_ENV=production
python << 'EOF'
import platform
print(f"Sistema: {platform.system()}")

from utils.printer import ThermalPrinter
from utils.printer_manager import listar_impresoras_windows
print("✓ utils imports OK")

from app import app
print("✓ app.py importado OK")
print(f"Blueprints: {list(app.blueprints.keys())}")
print(f"PRINTER_NAME: {app.config.get('PRINTER_NAME')}")
EOF
```

**Salida esperada:**
```
Sistema: Linux
✓ utils imports OK
✓ app.py importado OK
Blueprints: ['marcas', 'caracteristicas', ..., 'mostrador']
PRINTER_NAME: None
```

Si `printers` aparece en la lista de blueprints, algo está mal.

---

## 📊 TABLA DE ARCHIVOS CRÍTICOS

| Archivo | Ubicación en PA | Verificación |
|---------|-----------------|--------------|
| `app.py` | `/home/josephmercury10/mysite/app.py` | `head -1 app.py` debe mostrar imports completos |
| `config.py` | `/home/josephmercury10/mysite/config.py` | `grep ProductionConfig config.py` debe encontrar |
| `printer.py` | `/home/josephmercury10/mysite/utils/printer.py` | `grep "HAS_WIN32" utils/printer.py` debe encontrar |
| `printer_manager.py` | `/home/josephmercury10/mysite/utils/printer_manager.py` | `grep "HAS_WIN32" utils/printer_manager.py` |
| `base.html` | `/home/josephmercury10/mysite/templates/base.html` | `grep "config.PRINTER_NAME" templates/base.html` |

---

## 🚨 ERRORES RESUELTOS

1. ✅ `NameError: name 'redirect' is not defined` → `app.py` actualizado
2. ✅ `ModuleNotFoundError: flask_mysqldb` → `pip install Flask-MySQLdb`
3. ✅ `ModuleNotFoundError: win32print` → `utils/printer*.py` con imports condicionales
4. ✅ `BuildError: printers.index` → `templates/base.html` con enlace condicional

---

## 🎉 CUANDO TODO FUNCIONE

Visita: `https://josephmercury10.pythonanywhere.com`

Deberías ver tu aplicación Mundo Waffles funcionando.

**Próximos pasos:**
1. Migrar datos de local a PA (exportar/importar SQL)
2. Subir imágenes de productos
3. Probar funcionalidad de delivery y mostrador
4. Configurar backups regulares

---

**¿Todo listo?** Sube los 5 archivos críticos, configura variables y WSGI, luego Reload. 🚀
