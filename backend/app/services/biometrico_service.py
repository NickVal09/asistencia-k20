"""
Cliente biométrico real para el ZKTeco K20 (pyzk).

SOLO LECTURA. Este módulo nunca elimina marcaciones, usuarios, huellas ni
configuración del reloj: únicamente consulta información y marcaciones.
No se usan clear_attendance(), clear_data(), delete_user() ni disable_device().

El reloj original (ZLM60_TFT / Attendance Management Program) sigue siendo
el sistema de gestión; aquí solo se descargan los eventos para consultarlos
en MySQL. Se usan timeouts y reintentos limitados para no interferir.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class BiometricoService:
    def __init__(
        self,
        ip: Optional[str] = None,
        port: Optional[int] = None,
        platform: Optional[str] = None,
        timeout: Optional[int] = None,
        reintentos: Optional[int] = None,
    ):
        self.ip = ip or settings.ZK_DEVICE_IP
        self.port = int(port or settings.ZK_DEVICE_PORT)
        self.platform = platform or settings.ZK_DEVICE_PLATFORM
        self.timeout = int(timeout or settings.ZK_TIMEOUT_SEGUNDOS)
        self.reintentos = max(int(reintentos if reintentos is not None else settings.ZK_REINTENTOS), 1)
        self.is_connected = False

    # ------------------------------------------------------------------
    # Configuración (sin abrir sockets)
    # ------------------------------------------------------------------
    def test_configuration(self) -> Dict[str, Any]:
        return {
            "dispositivo": settings.ZK_DEVICE_NAME,
            "ip_configurada": self.ip,
            "puerto_configurado": self.port,
            "plataforma": self.platform,
            "timeout_segundos": self.timeout,
            "reintentos": self.reintentos,
            "mensaje": "Parámetros del K20 cargados. La conexión real se comprueba al sincronizar.",
        }

    def simulate_status_check(self) -> Dict[str, Any]:
        """Estado estático (compatibilidad). Nunca representa una conexión real."""
        return {
            "online": False,
            "modo": "historico_local",
            "ip": self.ip,
            "puerto": self.port,
            "plataforma": self.platform,
            "protocolo": "ZKTeco UDP/TCP Standalone SDK",
        }

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------
    def _nueva_conexion(self):
        from zk import ZK  # import diferido: el servidor arranca aunque falte pyzk

        zk = ZK(
            self.ip,
            port=self.port,
            timeout=self.timeout,
            force_udp=False,
            ommit_ping=True,
        )
        return zk.connect()

    def _con_reintentos(self, operacion, descripcion: str):
        """Ejecuta una operación con conexión nueva y reintentos limitados."""
        ultimo_error: Optional[Exception] = None
        for intento in range(1, self.reintentos + 1):
            conn = None
            try:
                conn = self._nueva_conexion()
                self.is_connected = True
                return operacion(conn)
            except Exception as exc:  # noqa: BLE001
                ultimo_error = exc
                logger.warning(
                    "[K20] %s falló (intento %s/%s): %s",
                    descripcion,
                    intento,
                    self.reintentos,
                    exc,
                )
                if intento < self.reintentos:
                    time.sleep(min(2 * intento, 5))
            finally:
                self.is_connected = False
                if conn is not None:
                    try:
                        conn.disconnect()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("[K20] Error al desconectar: %s", exc)
        raise RuntimeError(f"{descripcion}: {ultimo_error}") from ultimo_error

    # ------------------------------------------------------------------
    # Prueba de conexión (solo lectura, rápida)
    # ------------------------------------------------------------------
    def probar_conexion(self, leer_marcaciones: bool = False) -> Dict[str, Any]:
        """
        Abre una conexión, consulta datos de identificación del equipo y se
        desconecta. No modifica nada en el dispositivo.
        """
        inicio = time.time()

        def _operacion(conn) -> Dict[str, Any]:
            datos: Dict[str, Any] = {
                "nombre": _seguro(conn.get_device_name),
                "serie": _seguro(conn.get_serialnumber),
                "firmware": _seguro(conn.get_firmware_version),
                "plataforma": _seguro(conn.get_platform),
                "hora_dispositivo": _seguro(conn.get_time),
            }
            if leer_marcaciones:
                registros = conn.get_attendance()
                datos["total_marcaciones_dispositivo"] = len(registros)
            return datos

        try:
            datos = self._con_reintentos(_operacion, "Prueba de conexión")
            return {
                "conexion_ok": True,
                "mensaje": "Conexión comprobada con el reloj K20.",
                "duracion_segundos": round(time.time() - inicio, 2),
                "detalles": datos,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "conexion_ok": False,
                "mensaje": f"Sin conexión con el reloj K20: {exc}",
                "duracion_segundos": round(time.time() - inicio, 2),
                "detalles": {
                    "ip": self.ip,
                    "puerto": self.port,
                    "error": str(exc),
                },
            }

    # ------------------------------------------------------------------
    # Lectura completa de marcaciones
    # ------------------------------------------------------------------
    def leer_marcaciones(self) -> List[Dict[str, Any]]:
        """
        Descarga completa de marcaciones (get_attendance). Devuelve una lista
        de diccionarios con los campos originales:
        uid, user_id, timestamp, status, punch.
        """
        inicio = time.time()
        registros = self._con_reintentos(lambda conn: conn.get_attendance(), "Lectura de marcaciones")
        logger.info(
            "[K20] %s marcaciones leídas en %.1fs",
            len(registros),
            time.time() - inicio,
        )

        resultado: List[Dict[str, Any]] = []
        for r in registros:
            ts = getattr(r, "timestamp", None)
            if not isinstance(ts, datetime):
                continue
            resultado.append(
                {
                    "uid": getattr(r, "uid", None),
                    "user_id": str(getattr(r, "user_id", "")).strip(),
                    "timestamp": ts.replace(microsecond=0),
                    "status": int(getattr(r, "status", 0) or 0),
                    "punch": int(getattr(r, "punch", 0) or 0),
                }
            )
        return resultado


def _seguro(fn) -> Any:
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return None
