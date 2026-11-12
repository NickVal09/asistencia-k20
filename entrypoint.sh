#!/bin/sh
# Punto de entrada del contenedor: espera a MySQL, crea la BD si no existe,
# aplica migraciones y arranca el servicio unico (web + API).
# No requiere scripts de Windows ni terminales.

set -e

APP_PORT="${PORT:-${APP_PORT:-5173}}"
MYSQL_HOST="${MYSQL_SERVER:-db}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
MYSQL_DB="${MYSQL_DB:-asistencia_k20}"

echo "[entrypoint] Configuracion: host=${MYSQL_HOST} port=${MYSQL_PORT} db=${MYSQL_DB} port_app=${APP_PORT}"

# 1. Esperar a que MySQL acepte conexiones TCP.
#    Si no aparece, NO se aborta: el servicio arranca igual y la web muestra el
#    error de conexion con su boton "Reintentar" (mejor que una pagina caida).
echo "[entrypoint] Esperando a MySQL en ${MYSQL_HOST}:${MYSQL_PORT} ..."
intentos=0
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect(('${MYSQL_HOST}', ${MYSQL_PORT}))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    intentos=$((intentos + 1))
    if [ "$intentos" -ge 30 ]; then
        echo "[entrypoint] ADVERTENCIA: MySQL no respondio tras 60 s."
        echo "[entrypoint] Se arranca igualmente; revise MYSQL_SERVER/MYSQL_PORT/MYSQL_PASSWORD."
        break
    fi
    sleep 2
done
if [ "$intentos" -lt 30 ]; then
    echo "[entrypoint] MySQL disponible."
fi

# 2. Crear la base de datos si no existe (conectando a 'mysql' o sin BD)
echo "[entrypoint] Verificando/creando base de datos '${MYSQL_DB}' ..."
python -c "
import os, pymysql
host = os.environ.get('MYSQL_SERVER', 'db')
port = int(os.environ.get('MYSQL_PORT', '3306'))
user = os.environ.get('MYSQL_USER', 'root')
password = os.environ.get('MYSQL_PASSWORD', '')
db_name = os.environ.get('MYSQL_DB', 'asistencia_k20')
try:
    conn = pymysql.connect(host=host, port=port, user=user, password=password)
    with conn.cursor() as c:
        c.execute(f'CREATE DATABASE IF NOT EXISTS \`{db_name}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn.close()
    print(f'Base de datos {db_name} lista.')
except Exception as e:
    print(f'AVISO: no se pudo crear la BD ({e}). Se asume que ya existe.')
" || true

# 3. Aplicar migraciones
echo "[entrypoint] Aplicando migraciones (alembic upgrade head) ..."
cd /app/backend
migracion_ok=0
for i in 1 2 3 4 5; do
    if python -m alembic upgrade head; then
        echo "[entrypoint] Migraciones aplicadas correctamente."
        migracion_ok=1
        break
    fi
    echo "[entrypoint] Reintentando migraciones ($i/5)..."
    sleep 3
done
if [ "$migracion_ok" -ne 1 ]; then
    echo "[entrypoint] ADVERTENCIA: las migraciones no se aplicaron. La aplicacion puede fallar."
fi

# 4. Verificar que el frontend compilado existe
if [ ! -f /app/frontend/dist/index.html ]; then
    echo "[entrypoint] ADVERTENCIA: no se encontro /app/frontend/dist/index.html"
    ls -la /app/frontend/ 2>/dev/null || true
fi

# 5. Arrancar el servicio
echo "[entrypoint] Iniciando servicio en 0.0.0.0:${APP_PORT} ..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
