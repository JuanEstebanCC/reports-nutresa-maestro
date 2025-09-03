module.exports = {
  apps: [{
    name: 'nutresa-reports-api',
    script: 'run.py',
    interpreter: 'python3',
    cwd: '/var/www/reports-nutresa-maestro',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production',
      PORT: 8001,  // Puerto diferente para evitar conflictos
      HOST: '0.0.0.0'
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 8001,
      HOST: '0.0.0.0'
    },
    // Configuraciones de reinicio automático
    watch: false,
    max_memory_restart: '1G',
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s',
    
    // Logs
    log_file: '/var/log/pm2/nutresa-reports-combined.log',
    out_file: '/var/log/pm2/nutresa-reports-out.log',
    error_file: '/var/log/pm2/nutresa-reports-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm Z',
    
    // Auto restart on crash
    autorestart: true,
    
    // Environment variables
    env_file: '.env'
  }]
};