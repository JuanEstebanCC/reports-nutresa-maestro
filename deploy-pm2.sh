#!/bin/bash

# Deploy script para Nutresa Reports API con PM2
# Este script despliega la aplicación sin usar Apache
# EJECUTAR DESDE: /var/www/reports-nutresa-maestro

echo "🚀 Iniciando deployment de Nutresa Reports API..."

# Variables
PROJECT_DIR="/var/www/reports-nutresa-maestro"
SERVICE_NAME="nutresa-reports-api"

# Verificar que estamos en el directorio correcto
if [ ! -f "run.py" ]; then
    echo "❌ Error: Ejecuta este script desde /var/www/reports-nutresa-maestro"
    exit 1
fi

echo "✅ Directorio correcto detectado"

# Actualizar código (opcional si ya hiciste git pull)
echo "� Actualizando código desde Git..."
git pull origin main || echo "⚠️ Git pull falló o ya está actualizado"

# Crear entorno virtual de Python
echo "🐍 Configurando entorno virtual de Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "⚙️ Creando archivo .env..."
    cp config.example.env .env
    echo "❗ IMPORTANTE: Configura las variables de entorno en .env"
fi

# Crear directorios de logs
echo "📝 Configurando logs..."
sudo mkdir -p /var/log/pm2
sudo chown -R $USER:$USER /var/log/pm2

# Instalar PM2 si no está instalado
if ! command -v pm2 &> /dev/null; then
    echo "📦 Instalando PM2..."
    sudo npm install -g pm2
fi

# Detener aplicación si está corriendo
echo "⏹️ Deteniendo aplicación anterior..."
pm2 delete $SERVICE_NAME 2>/dev/null || true

# Iniciar aplicación con PM2
echo "▶️ Iniciando aplicación con PM2..."
pm2 start ecosystem.config.js --env production

# Configurar PM2 para que se inicie automáticamente
echo "🔧 Configurando PM2 para inicio automático..."
pm2 save
pm2 startup

# Mostrar status
echo "📊 Estado de la aplicación:"
pm2 status

# Mostrar información de conexión
echo ""
echo "✅ Deployment completado!"
echo "🌐 Tu API está disponible en: http://TU_IP_EC2:8001"
echo "📖 Documentación API: http://TU_IP_EC2:8001/docs"
echo "💚 Health check: http://TU_IP_EC2:8001/health"
echo ""
echo "📋 Comandos útiles:"
echo "  Ver logs:     pm2 logs $SERVICE_NAME"
echo "  Reiniciar:    pm2 restart $SERVICE_NAME"
echo "  Detener:      pm2 stop $SERVICE_NAME"
echo "  Estado:       pm2 status"
echo ""
echo "❗ No olvides:"
echo "  1. Configurar el Security Group de EC2 para permitir el puerto 8001"
echo "  2. Actualizar las variables en .env"
echo "  3. Configurar la base de datos MySQL"
