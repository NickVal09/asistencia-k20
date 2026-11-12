"""Healthcheck del contenedor.

Usa el puerto real del proceso (PORT de Dokploy, APP_PORT o 5173) para que el
contenedor no quede \"unhealthy\" cuando el puerto no es el de por defecto.
"""

import os
import sys
import urllib.request

puerto = (
    os.environ.get("PORT")
    or os.environ.get("APP_PORT")
    or "5173"
)
url = f"http://127.0.0.1:{puerto}/health"

try:
    with urllib.request.urlopen(url, timeout=5) as respuesta:
        if respuesta.status == 200:
            sys.exit(0)
        print(f"healthcheck: estado HTTP {respuesta.status}", file=sys.stderr)
        sys.exit(1)
except Exception as exc:  # noqa: BLE001
    print(f"healthcheck: {url} no responde ({exc})", file=sys.stderr)
    sys.exit(1)
