#!/bin/bash
# Script de verificación para PythonAnywhere
# Ejecutar en consola Bash de PA: bash check_deployment.sh

echo "========================================="
echo "  VERIFICACIÓN DE DESPLIEGUE - MUNDO WAFFLES"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables (ajustar según tu configuración)
USERNAME="josephmercury10"
PROJECT_DIR="mysite"
PROJECT_PATH="/home/$USERNAME/$PROJECT_DIR"
VENV_PATH="$PROJECT_PATH/venv"

echo "1. Verificando estructura de archivos..."
if [ -d "$PROJECT_PATH" ]; then
    echo -e "${GREEN}✓${NC} Directorio del proyecto existe: $PROJECT_PATH"
else
    echo -e "${RED}✗${NC} Directorio del proyecto NO existe: $PROJECT_PATH"
    exit 1
fi

# Verificar archivos críticos
FILES=("app.py" "config.py" "forms.py" "requirements_production.txt")
for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_PATH/$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file NO encontrado"
    fi
done

# Verificar carpetas críticas
DIRS=("routes" "src/models" "templates" "static" "utils")
for dir in "${DIRS[@]}"; do
    if [ -d "$PROJECT_PATH/$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ NO encontrada"
    fi
done

echo ""
echo "2. Verificando virtual environment..."
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment existe"
    
    # Activar venv y verificar Python
    source "$VENV_PATH/bin/activate"
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
    
    # Verificar módulos críticos
    echo ""
    echo "3. Verificando módulos Python instalados..."
    MODULES=("flask" "flask_mysqldb" "flask_sqlalchemy" "mysqlclient" "sqlalchemy" "wtforms")
    for module in "${MODULES[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            VERSION=$(python -c "import $module; print(getattr($module, '__version__', 'N/A'))" 2>/dev/null)
            echo -e "${GREEN}✓${NC} $module ($VERSION)"
        else
            echo -e "${RED}✗${NC} $module NO instalado"
        fi
    done
    
else
    echo -e "${RED}✗${NC} Virtual environment NO existe en: $VENV_PATH"
    echo -e "${YELLOW}→${NC} Crear con: python3.10 -m venv $VENV_PATH"
fi

echo ""
echo "4. Verificando variables de entorno..."
# Nota: Las variables del dashboard de PA no son accesibles en consola Bash
# Solo se inyectan en el proceso WSGI
echo -e "${YELLOW}!${NC} Las variables de entorno se verifican en el dashboard de PA:"
echo "   - APP_ENV"
echo "   - PA_DB_HOST"
echo "   - PA_DB_USER"
echo "   - PA_DB_PASSWORD"
echo "   - PA_DB_NAME"
echo "   - SECRET_KEY"
echo ""
echo -e "${YELLOW}→${NC} Verifica en: Web → tu app → Environment variables"

echo ""
echo "5. Verificando permisos de carpetas..."
if [ -w "$PROJECT_PATH/static/uploads" ]; then
    echo -e "${GREEN}✓${NC} static/uploads es escribible"
else
    echo -e "${YELLOW}!${NC} static/uploads podría no ser escribible"
    echo -e "${YELLOW}→${NC} Ejecutar: chmod 755 $PROJECT_PATH/static/uploads"
fi

echo ""
echo "6. Test de importación de app.py..."
cd "$PROJECT_PATH"
source "$VENV_PATH/bin/activate"

# Configurar variables temporales para test
export APP_ENV=production
export PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
export PA_DB_USER=josephmercury10
export PA_DB_PASSWORD=test  # Temporal para test de importación
export PA_DB_NAME=josephmercury10\$dbmundo
export SECRET_KEY=test_key_temporal

if python -c "from app import app; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} app.py se importa correctamente"
else
    echo -e "${RED}✗${NC} Error al importar app.py:"
    python -c "from app import app" 2>&1 | head -10
fi

echo ""
echo "========================================="
echo "  RESUMEN"
echo "========================================="
echo ""
echo "Si todos los checks son verdes (✓), procede a:"
echo "1. Configurar variables de entorno en dashboard PA"
echo "2. Configurar archivo WSGI (copiar de wsgi_pythonanywhere.py)"
echo "3. Configurar static files: /static/ → $PROJECT_PATH/static"
echo "4. Click en RELOAD"
echo ""
echo "Logs de errores en:"
echo "Web → Log files → Error log"
echo ""
