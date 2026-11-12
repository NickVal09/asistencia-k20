"""
Proceso independiente de sincronizacion automatica con el K20 (Fase 2).

Uso:
  cd backend
  ..\\venv\\Scripts\\python.exe scripts\\sync_auto.py --force   # prueba manual
  ..\\venv\\Scripts\\python.exe scripts\\sync_auto.py            # respeta SYNC_AUTOMATICA_ENABLED

Por defecto la sincronizacion automatica esta DESACTIVADA. Para activarla
defina SYNC_AUTOMATICA_ENABLED=True en backend/.env y un intervalo.

El proceso usa APScheduler con max_instances=1 y coalesce=True para evitar
ejecuciones solapadas dentro del mismo proceso, y MySQL GET_LOCK para evitar
ejecuciones solapadas entre procesos (servidor web vs. este daemon).
"""

import argparse
import logging
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.sync_service import SyncService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [sync-auto] %(levelname)s %(message)s",
)
logger = logging.getLogger("sync-auto")


def ejecutar_una_vez() -> None:
    db = SessionLocal()
    try:
        resultado = SyncService.ejecutar_automatica(db)
        logger.info("Resultado: %s", resultado)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error en sincronizacion automatica: %s", exc, exc_info=True)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincronizacion automatica K20")
    parser.add_argument(
        "--force", action="store_true", help="Ejecutar aunque SYNC_AUTOMATICA_ENABLED sea False"
    )
    parser.add_argument(
        "--now", action="store_true", help="Ejecutar una sincronizacion inmediatamente al iniciar"
    )
    args = parser.parse_args()

    if not settings.SYNC_AUTOMATICA_ENABLED and not args.force:
        logger.error(
            "La sincronizacion automatica esta DESACTIVADA por defecto. "
            "Defina SYNC_AUTOMATICA_ENABLED=True en backend/.env o use --force."
        )
        sys.exit(1)

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.error("Falta apscheduler. Instale con: pip install apscheduler")
        sys.exit(1)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        ejecutar_una_vez,
        trigger=IntervalTrigger(minutes=settings.SYNC_INTERVALO_MINUTOS),
        id="k20_sync_auto",
        name="Sincronizacion automatica K20",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    def _detener(signum, frame):
        logger.info("Señal %s recibida: deteniendo el programador.", signum)
        try:
            scheduler.shutdown(wait=False)
        except Exception:  # noqa: BLE001
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _detener)
    signal.signal(signal.SIGTERM, _detener)

    if args.now:
        logger.info("Ejecutando una sincronizacion inmediata antes de programar...")
        ejecutar_una_vez()

    logger.info(
        "Sincronizacion automatica activa cada %s minutos (Ctrl+C para detener).",
        settings.SYNC_INTERVALO_MINUTOS,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
