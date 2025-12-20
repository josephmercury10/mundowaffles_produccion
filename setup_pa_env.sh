#!/bin/bash
# Script para configurar variables de entorno en PythonAnywhere
# Uso: source setup_pa_env.sh

echo "🔧 Configurando variables de entorno para PythonAnywhere..."

# Configurar variables de base de datos
export PA_DB_HOST="josephmercury10.mysql.pythonanywhere-services.com"
export PA_DB_USER="josephmercury10"
export PA_DB_NAME="josephmercury10\$mundowaffles"

# Solicitar contraseña de forma segura
echo -n "Ingresa la contraseña de MySQL: "
read -s PA_DB_PASSWORD
export PA_DB_PASSWORD
echo ""

# Opcional: definir ambiente de producción explícitamente
export FLASK_ENV="production"

echo "✅ Variables configuradas:"
echo "   - PA_DB_HOST: $PA_DB_HOST"
echo "   - PA_DB_USER: $PA_DB_USER"
echo "   - PA_DB_NAME: $PA_DB_NAME"
echo "   - FLASK_ENV: $FLASK_ENV"
echo ""
echo "Ahora puedes ejecutar comandos de Alembic:"
echo "   alembic current"
echo "   alembic upgrade head"
