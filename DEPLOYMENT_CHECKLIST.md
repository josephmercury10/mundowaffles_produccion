# 🎯 PLAN DE DEPLOYMENT - CHECKLIST DE ACCIONES

## ✅ YA COMPLETADO EN LOCAL

- ✅ `app.py` - Auto-detección de entorno (PA_DB_HOST → production)
- ✅ `config.py` - ProductionConfig con variables de entorno
- ✅ `utils/printer.py` - Imports condicionales (Windows only)
- ✅ `utils/printer_manager.py` - Imports condicionales
- ✅ `templates/base.html` - Links condicionales para impresora
- ✅ `requirements_production.txt` - pymysql agregado
- ✅ Documentación: Todos los errores documentados

---

## 🚀 ACCIONES PENDIENTES EN PYTHONANYWHERE

### 1️⃣ SUBIR ARCHIVOS (Prioritario)

En PythonAnywhere Bash Console:

```bash
# Navega a tu proyecto
cd ~/mysite

# Opción A: Si usas Git (RECOMENDADO)
git pull origin main
# o
git pull origin master

# Opción B: Si subes archivos manualmente
# Baja estos archivos del editor a tu PC:
# - app.py (CON auto-detección)
# - config.py
# - requirements_production.txt
# 
# Luego súbelos a PythonAnywhere usando el editor web
```

**Archivos críticos a subir:**
- ✅ `app.py` (versión con auto-detección de entorno)
- ✅ `config.py` (con ProductionConfig)
- ✅ `utils/printer.py` (con imports condicionales)
- ✅ `utils/printer_manager.py` (con imports condicionales)

---

### 2️⃣ CONFIGURAR VARIABLES DE ENTORNO

Dashboard PA → **Web** (tu app) → **Environment variables**

**Agrega estas 6 variables:**

```
APP_ENV = production

PA_DB_HOST = josephmercury10.mysql.pythonanywhere-services.com
PA_DB_USER = josephmercury10
PA_DB_PASSWORD = <tu_password_mysql>
PA_DB_NAME = josephmercury10$mundowaffles  (¡SIN olvidar el prefijo!)
SECRET_KEY = <generar_con: python3 -c "import secrets; print(secrets.token_hex(32))">
```

⚠️ **CRÍTICO**: `PA_DB_NAME` debe incluir prefijo `josephmercury10$`

---

### 3️⃣ INSTALAR DEPENDENCIAS

En Bash Console:

```bash
cd ~/mysite
source venv/bin/activate

# Instalar pymysql (crucial para evitar socket error)
pip install pymysql

# Verificar que se instaló
pip list | grep pymysql
```

**Esperado:**
```
pymysql 1.1.1
```

---

### 4️⃣ RELOAD

Dashboard PA → **Web** → Botón **Reload** (verde)

Espera 10 segundos.

---

### 5️⃣ VERIFICAR LOGS

Dashboard PA → **Web** → **Error log** (revisar últimas líneas)

**Si ves esto = ✅ CORRECTO:**
```
[Mon Dec 04 12:34:56 2025] [FLASK] Entorno detectado: production
```

**Si ves esto = ❌ PROBLEMA:**
```
OperationalError: Can't connect to local MySQL server socket
```
→ Vuelve al paso 2️⃣ (falta configurar variables)

---

### 6️⃣ TEST DE CONEXIÓN

En Bash Console:

```bash
cd ~/mysite
source venv/bin/activate

python << 'EOF'
import os
print("\n=== DETECCIÓN DE ENTORNO ===")
print(f"APP_ENV: {os.environ.get('APP_ENV', 'NO SET')}")
print(f"PA_DB_HOST: {os.environ.get('PA_DB_HOST', 'NO SET')[:50]}...")

print("\n=== CARGANDO FLASK ===")
from app import app
with app.app_context():
    print("✅ Flask cargado sin errores")
    
    print("\n=== PROBANDO CONEXIÓN A BD ===")
    try:
        from utils.db import db
        db.session.execute("SELECT 1")
        print("✅ Conexión a BD exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)[:100]}")
EOF
```

**Esperado:**
```
=== DETECCIÓN DE ENTORNO ===
APP_ENV: production
PA_DB_HOST: josephmercury10.mysql.pythonanywhere-services.com

=== CARGANDO FLASK ===
✅ Flask cargado sin errores

=== PROBANDO CONEXIÓN A BD ===
✅ Conexión a BD exitosa
```

---

## 🧪 TEST MANUAL EN NAVEGADOR

Una vez que Reload esté hecho:

1. Abre: `https://josephmercury10.pythonanywhere.com`
2. Debe cargar sin errores
3. Si hay error → Revisa **Error log** en Dashboard PA

---

## 📊 POSIBLES ERRORES Y SOLUCIONES

| Error | Causa | Solución |
|-------|-------|----------|
| `OperationalError: Can't connect to local MySQL server socket` | No detectó producción | Verifica APP_ENV=production O PA_DB_HOST configuradas |
| `Access denied for user 'josephmercury10'` | Password incorrecto | Verifica PA_DB_PASSWORD exacto |
| `Unknown database 'mundowaffles'` | Falta prefijo en nombre BD | Usa `josephmercury10$mundowaffles` |
| `ImportError: No module named 'pymysql'` | No instalado pymysql | `pip install pymysql` |
| `ModuleNotFoundError: win32print` | Módulo Windows en Linux | Ya está arreglado (imports condicionales) |

---

## 🎯 ORDEN DE EJECUCIÓN

```
1. Subir archivos (app.py, config.py, utils/printer*.py)
   ↓
2. Configurar 6 variables de entorno en Dashboard
   ↓
3. pip install pymysql en Bash Console
   ↓
4. Click Reload
   ↓
5. Esperar 10 seg + revisar Error log
   ↓
6. Test: python test conexión en Bash Console
   ↓
7. Probar en navegador: https://josephmercury10.pythonanywhere.com
```

---

## 📋 CHECKLIST FINAL

- [ ] app.py subido (con auto-detección)
- [ ] config.py subido (con ProductionConfig)
- [ ] utils/printer*.py subidos (con imports condicionales)
- [ ] 6 variables de entorno configuradas
- [ ] pymysql instalado en venv
- [ ] Reload ejecutado
- [ ] Error log revisado (sin socket errors)
- [ ] Test conexión ejecutado en Bash
- [ ] Sitio accesible en navegador

---

## 🆘 SOPORTE RÁPIDO

Si necesitas reiniciar desde cero:

```bash
# Ver variables actuales
env | grep -E "APP_ENV|PA_DB"

# Recargar venv
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
pip install pymysql

# Testear
cd ~/mysite
python -c "from app import app; print('OK')"
```

---

**Una vez completado este checklist, tu app debería funcionar en PythonAnywhere sin errores de socket.** ✅
