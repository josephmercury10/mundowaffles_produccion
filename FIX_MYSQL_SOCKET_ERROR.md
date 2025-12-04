# 🔥 SOLUCIÓN: OperationalError - Can't connect to local MySQL server

## ❌ Error Actual
```
sqlalchemy.exc.OperationalError: (MySQLdb.OperationalError) (2002, 
"Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)")
```

## 🔍 Causa del Error

El código estaba inicializando **`Flask-MySQLdb`** en TODAS partes, incluyendo producción (PythonAnywhere).

`Flask-MySQLdb` intenta conectar usando un **socket local Unix** (`/var/run/mysqld/mysqld.sock`), que:
- ✅ Funciona en desarrollo local (Windows) porque es un alias para localhost:3309
- ❌ NO funciona en PythonAnywhere (Linux remoto) porque el socket no existe

**El problema**: El código intentaba usar `conexion = MySQL(app)` sin verificar el entorno.

---

## ✅ SOLUCIÓN APLICADA

He modificado `app.py` para:

1. **Deshabilitar `Flask-MySQLdb` en producción** (no es necesario)
2. **Usar solo `SQLAlchemy`** en PythonAnywhere (sí es necesario)
3. **Mantener ambos en desarrollo** (por compatibilidad con código existente)

### Cambio en `app.py`:

**Antes:**
```python
conexion = MySQL(app)  # ❌ Falla en PA
db.init_app(app)       # ✅ Funciona
```

**Después:**
```python
# En desarrollo: usar Flask-MySQLdb (local) además de SQLAlchemy
# En producción (PA): solo SQLAlchemy (MySQL remoto)
if ENV_NAME == 'development':
    from flask_mysqldb import MySQL
    conexion = MySQL(app)

# SQLAlchemy funciona en ambos entornos
db.init_app(app)       # ✅ Funciona siempre
```

**Resultado:**
- En **desarrollo** (Windows): `Flask-MySQLdb` + `SQLAlchemy` = funciona
- En **producción** (PA): Solo `SQLAlchemy` = funciona sin socket local

---

## 🚀 ACCIÓN REQUERIDA

**Sube el archivo actualizado a PythonAnywhere:**

Dashboard PA → **Files** → `/home/josephmercury10/mysite/`

**Archivo a reemplazar:**
- `app.py` (versión actualizada)

**Método manual:**
1. Abre `app.py` en el editor de PA
2. Reemplaza TODO con el contenido de `app.py` actualizado
3. Save

**Método Git:**
```bash
cd ~/mysite
git pull  # si usas repositorio
```

---

## ⚙️ VERIFICACIÓN

### Test local (Windows):
```powershell
# Debe funcionar igual que antes
python app.py
```

### Test en PythonAnywhere:
```bash
cd ~/mysite
source venv/bin/activate
export APP_ENV=production
export PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
export PA_DB_USER=josephmercury10
export PA_DB_PASSWORD=<tu_password>
export PA_DB_NAME=josephmercury10$dbmundo
export SECRET_KEY=test_key

python << 'EOF'
from app import app
with app.app_context():
    print("✓ App cargada sin errores de MySQL")
    print(f"Entorno: {app.config.get('ENV')}")
    print(f"DB Host: {app.config.get('MYSQL_HOST')}")
EOF
```

**Salida esperada:**
```
✓ App cargada sin errores de MySQL
Entorno: production
DB Host: josephmercury10.mysql.pythonanywhere-services.com
```

---

## 🔄 Después de subir

Dashboard PA → **Web** → Click **Reload**

Luego visita: `https://josephmercury10.pythonanywhere.com`

---

## 🧪 VERIFICACIÓN DE CONEXIÓN A BD

### Si aún hay errores de conexión:

```bash
# En PA Bash console
cd ~/mysite
source venv/bin/activate

# Test de conexión directa
mysql -h josephmercury10.mysql.pythonanywhere-services.com \
      -u josephmercury10 \
      -p<tu_password> \
      josephmercury10\$dbmundo \
      -e "SELECT 1"
```

Debería retornar `1` sin errores.

**Si la conexión falla:**
- Verifica password (debe estar correcto en variable `PA_DB_PASSWORD`)
- Verifica nombre de BD (debe incluir prefijo: `josephmercury10$`)
- Verifica que el usuario tenga permisos en la BD

---

## 📋 CHECKLIST ACTUALIZADO

Archivos que debes haber subido:

- [ ] ✅ `app.py` ← **ACTUALIZADO AHORA** (Flask-MySQLdb solo en dev)
- [ ] ✅ `config.py` (ProductionConfig)
- [ ] ✅ `utils/printer.py` (imports condicionales)
- [ ] ✅ `utils/printer_manager.py` (imports condicionales)
- [ ] ✅ `templates/base.html` (enlace condicional)
- [ ] ✅ Todas las carpetas: `routes/`, `src/`, `templates/`, `static/`, `utils/`, `forms/`
- [ ] ✅ Variables de entorno (6 variables)
- [ ] ✅ Archivo WSGI configurado
- [ ] ✅ Static files configurados

---

## 📊 PROGRESO DE ERRORES

| Error | Estado | Solución |
|-------|--------|----------|
| `redirect not defined` | ✅ RESUELTO | `app.py` actualizado |
| `flask_mysqldb not found` | ✅ RESUELTO | `pip install` |
| `win32print not found` | ✅ RESUELTO | imports condicionales |
| `BuildError printers.index` | ✅ RESUELTO | `templates/base.html` condicional |
| `Can't connect to MySQL socket` | ⚡ **EN PROCESO** | `app.py` con Flask-MySQLdb condicional |

---

## 🎯 PRÓXIMOS ERRORES POSIBLES

Una vez que la conexión funcione:

1. **"No such table: "** → Migraciones no ejecutadas, necesitas crear tablas en PA
2. **Errores de permisos en uploads** → `chmod 755 static/uploads`
3. **Imágenes no cargan** → Verificar path de static files
4. **Rutas 404** → Blueprints no registrados correctamente

---

**Siguiente paso:** Sube `app.py` actualizado y Reload. La BD debería conectar correctamente. 🚀
