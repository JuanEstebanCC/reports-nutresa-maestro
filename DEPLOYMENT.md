# Manual Deployment Guide - Reports Nutresa Maestro

Esta guía te ayudará a hacer el deployment manual de tu aplicación FastAPI en un servidor EC2 con Apache.

## Prerrequisitos

- Servidor EC2 con Ubuntu/Debian o CentOS/RHEL
- Acceso SSH al servidor
- Dominio configurado (opcional pero recomendado)
- Certificado SSL (para HTTPS)

## Opción 1: Deployment Automático (Recomendado)

### Paso 1: Conectarse al servidor
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Paso 2: Ejecutar el script de deployment
```bash
# Descargar el script
curl -O https://raw.githubusercontent.com/JuanEstebanCC/reports-nutresa-maestro/main/deploy.sh

# Hacer ejecutable
chmod +x deploy.sh

# Ejecutar como root
sudo ./deploy.sh
```

## Opción 2: Deployment Manual Paso a Paso

### Paso 1: Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Paso 2: Instalar dependencias del sistema
```bash
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    apache2 \
    libapache2-mod-wsgi-py3 \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    pkg-config
```

### Paso 3: Habilitar módulos de Apache
```bash
sudo a2enmod wsgi
sudo a2enmod rewrite
sudo a2enmod ssl
sudo a2enmod headers
```

### Paso 4: Crear directorio de la aplicación
```bash
sudo mkdir -p /var/www/reports-nutresa-maestro
cd /var/www/reports-nutresa-maestro
```

### Paso 5: Clonar el repositorio
```bash
sudo git clone https://github.com/JuanEstebanCC/reports-nutresa-maestro.git .
```

### Paso 6: Crear entorno virtual
```bash
sudo python3.12 -m venv venv
sudo chown -R www-data:www-data .
```

### Paso 7: Instalar dependencias de Python
```bash
sudo -u www-data ./venv/bin/pip install --upgrade pip
sudo -u www-data ./venv/bin/pip install -r requirements.txt
```

### Paso 8: Configurar Apache
```bash
# Copiar configuración
sudo cp apache-config.conf /etc/apache2/sites-available/reports-nutresa-maestro.conf

# Habilitar el sitio
sudo a2ensite reports-nutresa-maestro.conf

# Deshabilitar sitio por defecto (opcional)
sudo a2dissite 000-default.conf
```

### Paso 9: Configurar variables de entorno
```bash
# Crear archivo de configuración
sudo cp .env.example .env

# Editar con tus valores
sudo nano .env
```

### Paso 10: Probar y reiniciar Apache
```bash
# Probar configuración
sudo apache2ctl configtest

# Si todo está bien, reiniciar
sudo systemctl restart apache2
sudo systemctl enable apache2
```

## Configuración de Variables de Entorno

Crea un archivo `.env` en el directorio de la aplicación con el siguiente contenido:

```env
# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/database_name

# Security
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-domain.com"]

# Application Settings
DEBUG=False
LOG_LEVEL=info
```

## Configuración de Dominio

1. Edita el archivo de configuración de Apache:
```bash
sudo nano /etc/apache2/sites-available/reports-nutresa-maestro.conf
```

2. Cambia `your-domain.com` por tu dominio real:
```apache
ServerName tu-dominio.com
ServerAlias www.tu-dominio.com
```

3. Reinicia Apache:
```bash
sudo systemctl restart apache2
```

## Configuración SSL (HTTPS)

### Opción 1: Let's Encrypt (Gratuito)
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-apache

# Obtener certificado
sudo certbot --apache -d tu-dominio.com -d www.tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### Opción 2: Certificado propio
1. Sube tus archivos de certificado al servidor
2. Edita la configuración de Apache para apuntar a los archivos correctos
3. Reinicia Apache

## Verificación del Deployment

### Verificar que Apache esté corriendo
```bash
sudo systemctl status apache2
```

### Verificar que la aplicación responda
```bash
curl http://localhost/health
```

### Verificar logs
```bash
# Logs de Apache
sudo tail -f /var/log/apache2/reports-nutresa-maestro_error.log

# Logs de acceso
sudo tail -f /var/log/apache2/reports-nutresa-maestro_access.log
```

## Comandos Útiles

### Reiniciar la aplicación
```bash
sudo systemctl restart apache2
```

### Ver estado de Apache
```bash
sudo systemctl status apache2
```

### Probar configuración de Apache
```bash
sudo apache2ctl configtest
```

### Actualizar la aplicación
```bash
cd /var/www/reports-nutresa-maestro
sudo -u www-data git pull origin main
sudo -u www-data ./venv/bin/pip install -r requirements.txt
sudo systemctl restart apache2
```

## Troubleshooting

### Error 500 - Internal Server Error
1. Verificar logs de Apache: `sudo tail -f /var/log/apache2/error.log`
2. Verificar permisos: `sudo chown -R www-data:www-data /var/www/reports-nutresa-maestro`
3. Verificar que el archivo wsgi.py sea ejecutable: `sudo chmod +x /var/www/reports-nutresa-maestro/wsgi.py`

### Error de módulo WSGI
```bash
sudo apt install libapache2-mod-wsgi-py3
sudo a2enmod wsgi
sudo systemctl restart apache2
```

### Error de dependencias de Python
```bash
cd /var/www/reports-nutresa-maestro
sudo -u www-data ./venv/bin/pip install --upgrade pip
sudo -u www-data ./venv/bin/pip install -r requirements.txt
```

## Estructura Final del Servidor

```
/var/www/reports-nutresa-maestro/
├── app/
├── static/
├── venv/
├── wsgi.py
├── requirements.txt
├── .env
└── ...
```

## URLs de la API

Una vez desplegada, tu API estará disponible en:
- `http://tu-dominio.com/` - Página principal
- `http://tu-dominio.com/health` - Health check
- `http://tu-dominio.com/api/v1/` - Endpoints de la API

## Seguridad

1. **Firewall**: Configura el firewall para permitir solo puertos 80 y 443
2. **SSL**: Usa HTTPS en producción
3. **Variables de entorno**: Nunca subas el archivo `.env` al repositorio
4. **Permisos**: Mantén permisos restrictivos en archivos sensibles
5. **Updates**: Mantén el sistema y dependencias actualizadas

## Monitoreo

Considera implementar:
- Logs de aplicación
- Monitoreo de uptime
- Alertas de error
- Backup de base de datos
