#!/bin/bash

# Script de deployment rápido - EJECUTAR desde /var/www/reports-nutresa-maestro

echo "🚀 Deployment rápido de Nutresa Reports API"
echo "==============================================="

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "🐍 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo .env..."
    cp config.example.env .env
    echo "❗ IMPORTANTE: Configura las variables en .env antes de continuar"
    echo "   Presiona Enter cuando hayas configurado .env..."
    read
fi

# Crear directorios de logs
sudo mkdir -p /var/log/pm2
sudo chown -R $USER:$USER /var/log/pm2

# Instalar PM2 si no existe
if ! command -v pm2 &> /dev/null; then
    echo "📦 Instalando PM2..."
    sudo npm install -g pm2
fi

# Detener aplicación anterior
echo "⏹️ Deteniendo aplicación anterior..."
pm2 delete nutresa-reports-api 2>/dev/null || true

# Iniciar aplicación
echo "▶️ Iniciando aplicación..."
pm2 start ecosystem.config.js --env production

# Configurar autostart
pm2 save
pm2 startup | grep "sudo" | sh 2>/dev/null || true

echo ""
echo "✅ ¡Deployment completado!"
echo "🌐 API disponible en: http://$(curl -s ifconfig.me):8001"
echo "📖 Docs: http://$(curl -s ifconfig.me):8001/docs"
echo "💚 Health: http://$(curl -s ifconfig.me):8001/health"
echo ""
echo "📊 Estado actual:"
pm2 status
