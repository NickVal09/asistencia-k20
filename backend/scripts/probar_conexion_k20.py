"""
Prueba de conexión SOLO LECTURA con el biométrico ZKTeco K20.

No modifica, borra ni reinicia nada en el dispositivo: únicamente consulta
información y marcaciones. Uso:

    cd backend
    .\\venv\\Scripts\\python.exe scripts\\probar_conexion_k20.py

Variables opcionales: ZK_DEVICE_IP, ZK_DEVICE_PORT.
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402


def main() -> int:
    try:
        from zk import ZK
    except ImportError:
        print("ERROR: falta la libreria pyzk. Instala con: pip install pyzk")
        return 1

    ip = os.getenv("ZK_DEVICE_IP", settings.ZK_DEVICE_IP)
    port = int(os.getenv("ZK_DEVICE_PORT", settings.ZK_DEVICE_PORT))
    print(f"Conectando (solo lectura) a {ip}:{port} ...")

    zk = ZK(ip, port=port, timeout=10, force_udp=False, ommit_ping=True)
    conn = None
    inicio = time.time()
    try:
        conn = zk.connect()
        print("Conexion establecida.")
        print(f"  Nombre     : {conn.get_device_name()}")
        print(f"  Serie      : {conn.get_serialnumber()}")
        print(f"  Firmware   : {conn.get_firmware_version()}")
        print(f"  Plataforma : {conn.get_platform()}")
        print(f"  Hora reloj : {conn.get_time()}")

        print("Leyendo marcaciones (get_attendance)...")
        registros = conn.get_attendance()
        print(f"  Registros leidos: {len(registros)}")
        if registros:
            muestra = registros[:3] + registros[-3:]
            for r in muestra:
                print(
                    f"    user_id={r.user_id} ts={r.timestamp} "
                    f"status={r.status} punch={r.punch}"
                )
            futuras = sum(1 for r in registros if r.timestamp.year > datetime.now().year)
            print(f"  Registros con anio futuro: {futuras}")
        print(f"Duracion total: {round(time.time() - inicio, 2)} s")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR de conexion/lectura: {type(exc).__name__}: {exc}")
        return 2
    finally:
        if conn is not None:
            try:
                conn.disconnect()
                print("Desconectado del dispositivo.")
            except Exception as exc:  # noqa: BLE001
                print(f"Aviso al desconectar: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
