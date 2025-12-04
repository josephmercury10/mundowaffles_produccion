# SOLUCIÓN RÁPIDA A ERRORES ACTUALES EN PYTHONANYWHERE

## Error 1: `NameError: name 'redirect' is not defined`

**Causa**: Tienes una versión vieja de `app.py` en el servidor

**Solución**:
1. Sube el archivo `app.py` actualizado a PythonAnywhere
2. Asegúrate de que la primera línea sea exactamente:
   ```python
   from flask import Flask, render_template, jsonify, redirect, url_for
   ```

**Pasos**:
- En dashboard PA → **Files** → navega a `/home/josephmercury10/mysite/`
- Click en `app.py` para editarlo
- **Reemplaza TODO** el contenido con el `app.py` de tu proyecto local
- Save
- **Reload** la aplicación

---

## Error 2: `ModuleNotFoundError: No module named 'flask_mysqldb'`

**Causa**: El módulo no está instalado en el virtualenv de PythonAnywhere

**Solución**:

### Paso 1: Abrir Bash Console en PythonAnywhere
Dashboard → **Consoles** → **Bash**

### Paso 2: Activar virtualenv e instalar dependencias
```bash
cd ~/mysite
source venv/bin/activate
pip install Flask-MySQLdb mysqlclient
```

### Paso 3 (Opcional): Instalar todas las dependencias de producción
```bash
pip install -r requirements_production.txt
```

**Salida esperada**:
```
Successfully installed Flask-MySQLdb-2.0.0 mysqlclient-2.2.7
```

### Paso 4: Verificar instalación
```bash
python -c "import flask_mysqldb; print('OK')"
```

Debería imprimir: `OK`

### Paso 5: Reload
- Dashboard PA → **Web** → Click en **Reload** (botón verde)

---

## CHECKLIST COMPLETO DE DESPLIEGUE

### ☐ 1. Subir archivos actualizados
- [ ] `app.py` (con imports correctos)
- [ ] `config.py` (con ProductionConfig)
- [ ] Todas las carpetas: `routes/`, `src/`, `templates/`, `static/`, `utils/`, `forms/`
- [ ] `requirements_production.txt`

### ☐ 2. Crear virtualenv (si no existe)
```bash
cd ~/mysite
python3.10 -m venv venv
```

### ☐ 3. Instalar dependencias
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_production.txt
```

### ☐ 4. Configurar variables de entorno
Dashboard PA → **Web** → **Environment variables** → Add:

| Variable | Valor | Estado |
|----------|-------|--------|
| `APP_ENV` | `production` | [ ] |
| `PA_DB_HOST` | `josephmercury10.mysql.pythonanywhere-services.com` | [ ] |
| `PA_DB_USER` | `josephmercury10` | [ ] |
| `PA_DB_PASSWORD` | `<tu_password>` | [ ] |
| `PA_DB_NAME` | `josephmercury10$dbmundo` | [ ] |
| `SECRET_KEY` | `<genera_aleatorio>` | [ ] |

**Generar SECRET_KEY**:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### ☐ 5. Configurar archivo WSGI
Dashboard → **Web** → **Code** → click en archivo WSGI

**Copiar contenido de `wsgi_pythonanywhere.py`** (archivo creado en tu proyecto)

Verificar que las rutas sean correctas:
- `USERNAME = 'josephmercury10'`
- `PROJECT_DIR = 'mysite'`

### ☐ 6. Configurar archivos estáticos
Dashboard → **Web** → **Static files** → Add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/josephmercury10/mysite/static` |

### ☐ 7. Verificar nombre de base de datos
Dashboard → **Databases** → verifica el nombre exacto de tu BD

**Importante**: En PythonAnywhere las BDs tienen prefijo del usuario:
- Si creaste una BD llamada `dbmundo`, el nombre real es `josephmercury10$dbmundo`
- Usa ese nombre completo en `PA_DB_NAME`

### ☐ 8. Reload y verificar
- [ ] Click en **Reload** (botón verde)
- [ ] Visitar `https://josephmercury10.pythonanywhere.com`
- [ ] Revisar **Error log** si hay problemas

---

## VERIFICACIÓN DE LOGS

### Ver error log en tiempo real:
```bash
tail -f /var/log/josephmercury10.pythonanywhere.com.error.log
```

### Ver últimas 50 líneas del error log:
```bash
tail -50 /var/log/josephmercury10.pythonanywhere.com.error.log
```

---

## ERRORES COMUNES Y SOLUCIONES

### Error: `Access denied for user 'josephmercury10'@'%'`
- Verifica password en variables de entorno
- Verifica que el usuario tenga permisos en la BD (Databases → Permissions)

### Error: `Unknown database 'dbmundo'`
- El nombre de la BD debe incluir el prefijo: `josephmercury10$dbmundo`
- Actualiza variable `PA_DB_NAME`

### Error: `Table doesn't exist`
- Tu BD en PA está vacía, necesitas migrar/importar datos
- Opción 1: Exporta desde local e importa en PA (Databases → MySQL console)
- Opción 2: Ejecuta migraciones de Alembic

### Error: Páginas sin estilos CSS
- Verifica configuración de static files
- Verifica que carpeta `static/` esté subida completamente

---

## CONTACTO Y SOPORTE

Si los errores persisten después de seguir estos pasos:

1. **Copia el error completo** del Error log
2. **Verifica**:
   - Versión de Python en PA (debe ser 3.8+)
   - Todas las variables de entorno estén configuradas
   - Virtualenv esté activado en archivo WSGI
3. **Revisa** la documentación oficial: https://help.pythonanywhere.com/pages/Flask/

---

## COMANDOS ÚTILES

```bash
# Ver versión de Python
python --version

# Ver módulos instalados
pip list

# Verificar importación de app
python -c "from app import app; print('OK')"

# Ver estructura de carpetas
tree -L 2 ~/mysite  # o usa: ls -R ~/mysite

# Ver contenido de archivo
cat ~/mysite/app.py | head -20
```
