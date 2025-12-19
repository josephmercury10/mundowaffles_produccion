# Actualizar Base de Datos en PythonAnywhere

## ⚠️ Importante
Como estás usando la **misma base de datos** para desarrollo y producción, la migración **ya está aplicada** desde tu entorno local. Solo necesitas actualizar el código en PythonAnywhere.

## 📋 Pasos para actualizar PythonAnywhere

### 1️⃣ Subir archivos actualizados

Sube estos archivos modificados a PythonAnywhere:

**Modelos:**
- `src/models/Venta_model.py` (campo `notas` agregado a ProductoVenta)

**Migraciones:**
- `alembic/versions/20251218_add_notas_producto_venta.py` (nueva migración)

**Templates:**
- `templates/ventas/_partials/modal_extras.html` (campo de notas en modal delivery)
- `templates/ventas/_partials/modal_extras_mostrador.html` (campo de notas en modal mostrador)
- `templates/ventas/mostrador/_partials/carrito_items.html` (mostrar notas en carrito)
- `templates/ventas/mostrador/_partials/items_pedido.html` (mostrar notas en items)

**Rutas:**
- `routes/mostrador.py` (manejo de notas en backend)
- `routes/delivery.py` (manejo de notas en backend)

**Utils:**
- `utils/printer.py` (imprimir notas en comandas)

### 2️⃣ Conectarse a PythonAnywhere

```bash
# Abrir consola Bash en PythonAnywhere
# Dashboard > Consoles > Bash
```

### 3️⃣ Verificar estado de la migración

```bash
cd ~/mundowaffles_produccion

# Activar entorno virtual (si tienes uno)
source env/bin/activate

# Ver migración actual
python -m alembic current

# Debería mostrar: 20251218_add_notas (head)
# Si ya está aplicada, NO hacer nada más
```

### 4️⃣ Si la migración NO está aplicada (poco probable)

**SOLO si `alembic current` NO muestra `20251218_add_notas`:**

```bash
# Ver qué migraciones están pendientes
python -m alembic history

# Aplicar migración
python -m alembic upgrade head

# Verificar que se aplicó
python -m alembic current
```

### 5️⃣ Reiniciar aplicación web

```bash
# Desde el dashboard de PythonAnywhere:
# Web > Reload tu-usuario.pythonanywhere.com
```

O usando el botón verde "Reload" en la pestaña Web.

### 6️⃣ Verificar funcionamiento

1. Accede a tu sitio en PythonAnywhere
2. Ve a Mostrador o Delivery
3. Agrega un producto
4. Verifica que aparezca el campo "Instrucciones especiales" en el modal
5. Prueba agregar una nota: "sin cebolla"
6. Verifica que la nota aparezca en el carrito y en el pedido

## 🔍 Troubleshooting

### Error: "No module named 'alembic'"

```bash
pip install alembic
```

### Error: "Can't locate revision identified by '20251208_add_metodos_pago'"

La base de datos está desincronizada. Verifica el estado:

```bash
# Ver estado en BD
python -c "from utils.db import db; import app; with app.app.app_context(): result = db.session.execute(db.text('SELECT * FROM alembic_version')); print([r[0] for r in result])"
```

### Error: "Requested revision overlaps"

Hay registros duplicados en `alembic_version`. Ejecuta:

```bash
python -c "from utils.db import db; import app; with app.app.app_context(): db.session.execute(db.text('DELETE FROM alembic_version WHERE version_num != (SELECT MAX(version_num) FROM (SELECT version_num FROM alembic_version) as t)')); db.session.commit(); print('Duplicados eliminados')"
```

## 📝 Resumen de cambios

### Campo agregado a la BD:
```sql
ALTER TABLE producto_venta ADD COLUMN notas TEXT NULL COMMENT 'Instrucciones especiales del cliente';
```

### Funcionalidad:
- Campo de texto opcional (máximo 200 caracteres)
- Se muestra en modal de extras de productos
- Se guarda en cada `ProductoVenta`
- Se imprime en comandas de cocina con formato destacado
- Se visualiza en carrito y detalles del pedido

## ⚡ Opción rápida (si la migración ya está aplicada)

Si ya aplicaste la migración localmente y comparten la BD:

1. Sube solo los archivos de código (no ejecutes migración)
2. Reload de la aplicación web
3. ¡Listo!

La BD ya tiene el campo `notas` porque lo aplicaste localmente.
