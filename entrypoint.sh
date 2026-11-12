#!/bin/sh
# Punto de entrada del contenedor: espera a MySQL, aplica migraciones y arranca
# el servicio unico (web + API). No requiere scripts de Windows ni terminales.

set -e

APP_PORT="${APP_PORT:-5173}"
MYSQL_HOST="${MYSQL_SERVER:-db}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

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
    if [ "$intentos" -ge 60 ]; then
        echo "[entrypoint] MySQL no respondio tras 60 intentos. Abortando."
        exit 1
    fi
    sleep 2
done
echo "[entrypoint] MySQL disponible."

echo "[entrypoint] Aplicando migraciones de base de datos (alembic upgrade head) ..."
cd /app/backend
for i in 1 2 3 4 5; do
    if python -m alembic upgrade head; then
        echo "[entrypoint] Migraciones aplicadas."
        break
    fi
    echo "[entrypoint] Reintentando migraciones ($i/5)..."
    sleep 3
done

echo "[entrypoint] Iniciando servicio en 0.0.0.0:${APP_PORT} ..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
