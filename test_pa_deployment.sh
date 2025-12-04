#!/bin/bash
# test_pa_deployment.sh
# Script de prueba rápida para PythonAnywhere
# Ejecutar: bash test_pa_deployment.sh

echo "=================================="
echo "TEST RÁPIDO - MUNDO WAFFLES PA"
echo "=================================="
echo ""

cd ~/mysite
source venv/bin/activate

echo "1. Python version:"
python --version
echo ""

echo "2. Test imports críticos:"
python << 'EOF'
try:
    import flask
    print("✓ Flask:", flask.__version__)
except:
    print("✗ Flask no instalado")

try:
    import flask_mysqldb
    print("✓ Flask-MySQLdb")
except Exception as e:
    print("✗ Flask-MySQLdb:", str(e))

try:
    import MySQLdb
    print("✓ mysqlclient (MySQLdb)")
except Exception as e:
    print("✗ mysqlclient:", str(e))

try:
    from flask_sqlalchemy import SQLAlchemy
    print("✓ Flask-SQLAlchemy")
except:
    print("✗ Flask-SQLAlchemy no instalado")
EOF

echo ""
echo "3. Test importación de app.py:"
export APP_ENV=production
export PA_DB_HOST=josephmercury10.mysql.pythonanywhere-services.com
export PA_DB_USER=josephmercury10
export PA_DB_PASSWORD=test123
export PA_DB_NAME=josephmercury10\$dbmundo
export SECRET_KEY=test_key

python << 'EOF'
try:
    from app import app
    print("✓ app.py se importa correctamente")
    print("  Configuración activa:", app.config.get('DEBUG'))
    print("  DB Host:", app.config.get('MYSQL_HOST'))
except Exception as e:
    print("✗ Error importando app.py:")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "4. Verificar archivos críticos:"
for file in app.py config.py forms.py; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file NO encontrado"
    fi
done

echo ""
echo "5. Verificar carpetas:"
for dir in routes src templates static utils; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ✗ $dir/ NO encontrada"
    fi
done

echo ""
echo "6. Primera línea de app.py (debe tener imports):"
head -1 app.py

echo ""
echo "=================================="
echo "Si ves errores arriba, corrígelos antes de Reload"
echo "=================================="
