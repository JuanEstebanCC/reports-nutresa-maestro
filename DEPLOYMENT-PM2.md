# Deployment con PM2 en EC2 (Proyecto ya en servidor)

Esta guía te permitirá desplegar tu aplicación FastAPI usando PM2 en EC2, accesible por IP sin conflictos con Apache.

## 🚀 Pasos para el Deployment (Proyecto ya en /var/www/)

### 1. Conectarse al servidor EC2

```bash
ssh -i tu-key.pem ubuntu@TU_IP_EC2
```

### 2. Navegar al proyecto

```bash
cd /var/www/reports-nutresa-maestro
```

### 3. Instalar dependencias del sistema (si no están instaladas)

```bash
# Actualizar sistema
sudo apt update

# Instalar Node.js y PM2 si no están instalados
sudo apt install nodejs npm -y
sudo npm install -g pm2

# Verificar Python 3
python3 --version
```

### 4. Ejecutar el script de deployment

```bash
# Hacer ejecutable el script
chmod +x deploy-pm2.sh

# Ejecutar deployment
./deploy-pm2.sh
```

### 4. Configurar Security Group

En tu consola AWS EC2:
1. Ve a Security Groups
2. Selecciona el Security Group de tu instancia
3. Añade regla de entrada:
   - Type: Custom TCP
   - Port Range: 8001
   - Source: 0.0.0.0/0 (o tu IP específica para mayor seguridad)

### 5. Configurar variables de entorno

```bash
cd /var/www/reports-nutresa-maestro
nano .env
```

Configura las variables necesarias (base de datos, etc.)

## 🔧 Gestión de la aplicación

### Comandos PM2 útiles:

```bash
# Ver estado de todas las aplicaciones
pm2 status

# Ver logs en tiempo real
pm2 logs nutresa-reports-api

# Reiniciar la aplicación
pm2 restart nutresa-reports-api

# Detener la aplicación
pm2 stop nutresa-reports-api

# Eliminar la aplicación de PM2
pm2 delete nutresa-reports-api

# Recargar configuración
pm2 reload ecosystem.config.js --env production

# Monitoreo en tiempo real
pm2 monit
```

### Acceso a la aplicación:

- **API Base**: `http://TU_IP_EC2:8001`
- **Documentación**: `http://TU_IP_EC2:8001/docs`
- **Health Check**: `http://TU_IP_EC2:8001/health`

## 🛡️ Ventajas de esta configuración

1. **Sin conflictos con Apache**: Usa puerto 8001, Apache puede seguir en 80/443
2. **Auto-restart**: PM2 reinicia automáticamente si la app falla
3. **Logs organizados**: Todos los logs en `/var/log/pm2/`
4. **Fácil gestión**: Comandos simples de PM2 para administrar
5. **Startup automático**: Se inicia automáticamente al reiniciar el servidor
6. **Monitoreo**: PM2 incluye herramientas de monitoreo built-in

## 🔍 Troubleshooting

### Si la aplicación no inicia:
```bash
# Ver logs detallados
pm2 logs nutresa-reports-api --lines 50

# Verificar que Python y dependencias estén instaladas
which python3
pip list
```

### Si no puedes acceder desde el navegador:
1. Verifica que el Security Group permita el puerto 8001
2. Verifica que el firewall local no esté bloqueando
3. Prueba con `curl localhost:8001` desde el servidor

### Para actualizar la aplicación:
```bash
cd /var/www/reports-nutresa-maestro
git pull origin main  # Si usas Git
pm2 restart nutresa-reports-api
```

Esta configuración te permitirá tener tu API corriendo de forma estable y profesional usando solo la IP del servidor, sin interferir con tus otros subdominios en Apache.
