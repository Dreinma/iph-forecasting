# Gunicorn Configuration untuk Production
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5001"
backlog = 2048

# Worker processes (reduced to prevent database initialization conflicts)
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/iph-forecasting-access.log"
errorlog = "/var/log/iph-forecasting-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "iph-forecasting"

# Server mechanics
daemon = False
pidfile = None  # Let Supervisor handle PID management
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (jika diperlukan direct SSL)
keyfile = None
certfile = None

# Environment variables
raw_env = [
    f"FLASK_ENV={os.environ.get('FLASK_ENV', 'production')}",
    f"SECRET_KEY={os.environ.get('SECRET_KEY', '')}",
]

