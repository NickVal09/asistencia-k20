"""
Servicio de sincronización real con el biométrico ZKTeco K20 (Fase 2).

Garantías:
- Solo lectura sobre el dispositivo (nunca borra ni modifica datos).
- Descarga completa de marcaciones + deduplicación por hash (igual que el CSV).
- Conserva intactos los registros existentes y detecta fechas futuras.
- Exclusión mutua entre procesos con MySQL GET_LOCK('k20_sync').
- La tarea manual corre en segundo plano: sobrevive al cierre del navegador.
- Si el servidor se reinicia a mitad de una ejecución, la ejecución queda
  marcada como 'interrumpido' y los registros ya insertados se conservan.
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.dispositivo import Dispositivo
from app.models.ejecucion import EjecucionSincronizacion
from app.models.marcacion import Marcacion
from app.models.trabajador import Trabajador
from app.services.biometrico_service import BiometricoService
from app.services.import_service import ImportService

logger = logging.getLogger(__name__)


class SincronizacionEnCurso(RuntimeError):
    pass


class SyncService:
    LOCK_NAME = "k20_sync"
    BATCH_SIZE = 1000
    _lock_proceso = threading.Lock()

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    @staticmethod
    @contextmanager
    def _lock_base_datos():
        """
        Exclusión mutua entre procesos mediante GET_LOCK de MySQL.
        El lock vive en la conexión, por eso se mantiene abierta hasta el final.
        """
        conn = engine.connect()
        adquirido = False
        try:
            resultado = conn.execute(
                text("SELECT GET_LOCK(:nombre, 0)"), {"nombre": SyncService.LOCK_NAME}
            ).scalar()
            adquirido = resultado == 1
            yield adquirido
        finally:
            if adquirido:
                try:
                    conn.execute(
                        text("SELECT RELEASE_LOCK(:nombre)"), {"nombre": SyncService.LOCK_NAME}
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[sync] No se pudo liberar el lock: %s", exc)
            conn.close()

    @staticmethod
    def marcar_ejecuciones_colgadas(db) -> int:
        """
        Marca como 'interrumpido' las ejecuciones que quedaron en_progreso
        tras un reinicio del servidor. No borra nada.
        """
        limite = datetime.utcnow() - timedelta(minutes=settings.SYNC_EJECUCION_COLGADA_MINUTOS)
        colgadas = (
            db.query(EjecucionSincronizacion)
            .filter(
                EjecucionSincronizacion.origen == "biometrico_k20",
                EjecucionSincronizacion.estado == "en_progreso",
                EjecucionSincronizacion.iniciado_el < limite,
            )
            .all()
        )
        for ej in colgadas:
            ej.estado = "interrumpido"
            ej.finalizado_el = datetime.utcnow()
            ej.duracion_segundos = round(
                (ej.finalizado_el - ej.iniciado_el).total_seconds(), 2
            )
            ej.mensaje_detalle = (
                (ej.mensaje_detalle or "")
                + " | Ejecución interrumpida (posible reinicio del servidor)."
            ).strip(" |")
        if colgadas:
            db.commit()
            logger.warning("[sync] %s ejecuciones colgadas marcadas como interrumpidas.", len(colgadas))
        return len(colgadas)

    @staticmethod
    def _ejecucion_activa(db) -> Optional[EjecucionSincronizacion]:
        return (
            db.query(EjecucionSincronizacion)
            .filter(
                EjecucionSincronizacion.origen == "biometrico_k20",
                EjecucionSincronizacion.estado == "en_progreso",
            )
            .order_by(EjecucionSincronizacion.id.desc())
            .first()
        )

    @staticmethod
    def _crear_ejecucion(db, modo: str) -> EjecucionSincronizacion:
        dispositivo = ImportService.get_or_create_default_device(db)
        ejecucion = EjecucionSincronizacion(
            origen="biometrico_k20",
            modo=modo,
            dispositivo_id=dispositivo.id,
            estado="en_progreso",
            conexion_ok=None,
            iniciado_el=datetime.utcnow(),
            mensaje_detalle="En cola: esperando turno de sincronización.",
        )
        db.add(ejecucion)
        db.commit()
        db.refresh(ejecucion)
        return ejecucion

    # ------------------------------------------------------------------
    # Inicio manual (en segundo plano)
    # ------------------------------------------------------------------
    @staticmethod
    def iniciar_manual(db) -> Dict[str, Any]:
        """
        Crea la ejecución y lanza un hilo en segundo plano. Responde de
        inmediato para no bloquear la petición HTTP.
        """
        SyncService.marcar_ejecuciones_colgadas(db)

        activa = SyncService._ejecucion_activa(db)
        if activa:
            return {
                "iniciado": False,
                "motivo": "en_curso",
                "ejecucion_id": activa.id,
                "estado": activa.estado,
                "mensaje": "Ya hay una sincronización con el K20 en curso.",
            }

        if SyncService._lock_proceso.locked():
            return {
                "iniciado": False,
                "motivo": "en_curso",
                "ejecucion_id": None,
                "estado": "en_progreso",
                "mensaje": "Ya hay una sincronización con el K20 en curso.",
            }

        ejecucion = SyncService._crear_ejecucion(db, modo="manual")
        hilo = threading.Thread(
            target=SyncService._ejecutar,
            args=(ejecucion.id, "manual"),
            name=f"k20-sync-manual-{ejecucion.id}",
            daemon=True,
        )
        hilo.start()
        return {
            "iniciado": True,
            "motivo": None,
            "ejecucion_id": ejecucion.id,
            "estado": "en_progreso",
            "mensaje": "Sincronización iniciada. Puedes cerrar el navegador: la tarea continúa.",
        }

    # ------------------------------------------------------------------
    # Ejecución automática (proceso daemon; síncrona)
    # ------------------------------------------------------------------
    @staticmethod
    def ejecutar_automatica(db) -> Dict[str, Any]:
        SyncService.marcar_ejecuciones_colgadas(db)

        activa = SyncService._ejecucion_activa(db)
        if activa or SyncService._lock_proceso.locked():
            return {
                "ejecutado": False,
                "motivo": "en_curso",
                "mensaje": "Otra sincronización está en curso; se omite esta ejecución.",
            }

        ejecucion = SyncService._crear_ejecucion(db, modo="automatico")
        resultado = SyncService._ejecutar(ejecucion.id, "automatico")
        return {"ejecutado": True, **(resultado or {})}

    # ------------------------------------------------------------------
    # Núcleo de la sincronización
    # ------------------------------------------------------------------
    @staticmethod
    def _ejecutar(ejecucion_id: int, modo: str) -> Optional[Dict[str, Any]]:
        if not SyncService._lock_proceso.acquire(blocking=False):
            SyncService._fallar(ejecucion_id, "Otra sincronización está en curso (mismo servidor).", conectado=False)
            return None

        db = SessionLocal()
        inicio = time.time()
        conectado = False
        total_leidos = 0
        nuevos = 0
        duplicados = 0
        errores = 0
        sospechosas = 0
        ultima_valida: Optional[datetime] = None

        try:
            with SyncService._lock_base_datos() as adquirido:
                if not adquirido:
                    SyncService._fallar(
                        ejecucion_id,
                        "Otra sincronización con el K20 está en curso en otro proceso.",
                        conectado=False,
                    )
                    return None

                ejecucion = db.get(EjecucionSincronizacion, ejecucion_id)
                if not ejecucion:
                    logger.error("[sync] Ejecución %s no existe.", ejecucion_id)
                    return None

                dispositivo = (
                    db.get(Dispositivo, ejecucion.dispositivo_id)
                    if ejecucion.dispositivo_id
                    else ImportService.get_or_create_default_device(db)
                )

                SyncService._fase(db, ejecucion, "Conectando con el K20 y descargando marcaciones...")
                bio = BiometricoService()
                registros = bio.leer_marcaciones()
                conectado = True
                total_leidos = len(registros)

                ejecucion.total_leidos = total_leidos
                ejecucion.conexion_ok = True
                SyncService._fase(
                    db,
                    ejecucion,
                    f"{total_leidos} marcaciones leídas. Comparando con MySQL...",
                )

                existentes = {
                    h for (h,) in db.query(Marcacion.hash_deduplicacion).all() if h
                }
                anio_actual = datetime.now().year
                lote: List[Marcacion] = []
                usuarios_nuevos = set()

                for registro in registros:
                    try:
                        ts: datetime = registro["timestamp"]
                        user_id: str = registro["user_id"]
                        status_val: int = registro["status"]
                        punch_val: int = registro["punch"]

                        hash_dedup = ImportService.calculate_dedup_hash(
                            dispositivo.id,
                            user_id,
                            ts.strftime("%Y-%m-%d %H:%M:%S"),
                            status_val,
                            punch_val,
                        )

                        sospechosa = ts.year > anio_actual
                        if sospechosa:
                            sospechosas += 1
                        elif ultima_valida is None or ts > ultima_valida:
                            ultima_valida = ts

                        if hash_dedup in existentes:
                            duplicados += 1
                            continue
                        existentes.add(hash_dedup)

                        lote.append(
                            Marcacion(
                                uid=registro.get("uid"),
                                dispositivo_id=dispositivo.id,
                                ejecucion_id=ejecucion.id,
                                user_id=user_id,
                                timestamp=ts,
                                status=status_val,
                                punch=punch_val,
                                fecha_sospechosa=sospechosa,
                                motivo_sospecha=(
                                    f"fecha_futura_anio_{ts.year}" if sospechosa else None
                                ),
                                hash_deduplicacion=hash_dedup,
                            )
                        )
                        usuarios_nuevos.add(user_id)

                        if len(lote) >= SyncService.BATCH_SIZE:
                            insertados, conflictos = SyncService._insertar_lote(db, lote)
                            nuevos += insertados
                            duplicados += conflictos
                            lote = []
                            ejecucion.nuevos_registros = nuevos
                            ejecucion.duplicados_omitidos = duplicados
                            db.commit()
                    except Exception as exc:  # noqa: BLE001
                        errores += 1
                        logger.warning("[sync] Registro inválido omitido: %s", exc)

                if lote:
                    insertados, conflictos = SyncService._insertar_lote(db, lote)
                    nuevos += insertados
                    duplicados += conflictos

                if usuarios_nuevos:
                    SyncService._actualizar_trabajadores(db, usuarios_nuevos)

                ahora = datetime.utcnow()
                dispositivo.ultima_conexion_ok = ahora
                dispositivo.ultimo_sync = ahora
                dispositivo.ultimo_error = None
                dispositivo.ultimo_error_el = None
                dispositivo.ultimo_modo_conexion = modo

                ejecucion.estado = "completado"
                ejecucion.total_leidos = total_leidos
                ejecucion.nuevos_registros = nuevos
                ejecucion.duplicados_omitidos = duplicados
                ejecucion.errores = errores
                ejecucion.fechas_sospechosas_detectadas = sospechosas
                ejecucion.conexion_ok = True
                ejecucion.ultima_marcacion = ultima_valida
                ejecucion.finalizado_el = ahora
                ejecucion.duracion_segundos = round(time.time() - inicio, 2)
                ejecucion.mensaje_detalle = (
                    f"Sincronización {modo} completada en {ejecucion.duracion_segundos}s. "
                    f"Leídas: {total_leidos}, Nuevas: {nuevos}, "
                    f"Duplicadas: {duplicados}, Errores: {errores}."
                )
                db.commit()

                resultado = {
                    "ejecucion_id": ejecucion.id,
                    "estado": ejecucion.estado,
                    "total_leidos": total_leidos,
                    "nuevos_registros": nuevos,
                    "duplicados_omitidos": duplicados,
                    "errores": errores,
                    "fechas_sospechosas_detectadas": sospechosas,
                    "duracion_segundos": ejecucion.duracion_segundos,
                    "ultima_marcacion": ultima_valida,
                }
                logger.info("[sync] %s", ejecucion.mensaje_detalle)
                return resultado

        except Exception as exc:  # noqa: BLE001
            logger.error("[sync] Falló la sincronización: %s", exc, exc_info=True)
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                pass
            SyncService._fallar(
                ejecucion_id,
                f"Error durante la sincronización: {exc}",
                conectado=conectado,
                total_leidos=total_leidos,
                nuevos=nuevos,
                duplicados=duplicados,
                errores=errores + 1,
                duracion=round(time.time() - inicio, 2),
                modo=modo,
            )
            return None
        finally:
            db.close()
            if SyncService._lock_proceso.locked():
                try:
                    SyncService._lock_proceso.release()
                except RuntimeError:
                    pass

    @staticmethod
    def _insertar_lote(db, lote: List[Marcacion]) -> tuple:
        """Inserta un lote. Si hay colisión de hash, reintenta fila por fila."""
        try:
            db.bulk_save_objects(lote)
            db.commit()
            return len(lote), 0
        except IntegrityError:
            db.rollback()
            insertados = 0
            conflictos = 0
            for marcacion in lote:
                try:
                    db.add(marcacion)
                    db.commit()
                    insertados += 1
                except IntegrityError:
                    db.rollback()
                    conflictos += 1
            return insertados, conflictos

    @staticmethod
    def _actualizar_trabajadores(db, usuarios: set) -> None:
        """Recalcula estadísticas desde MySQL para los usuarios con registros nuevos."""
        max_valido = func.max(
            case((Marcacion.fecha_sospechosa.is_(False), Marcacion.timestamp), else_=None)
        )
        filas = (
            db.query(
                Marcacion.user_id,
                func.count(Marcacion.id),
                func.min(Marcacion.timestamp),
                max_valido,
            )
            .filter(Marcacion.user_id.in_(list(usuarios)))
            .group_by(Marcacion.user_id)
            .all()
        )
        for user_id, total, primer_ts, ultimo_ts in filas:
            trabajador = db.query(Trabajador).filter(Trabajador.user_id == user_id).first()
            if trabajador:
                trabajador.total_marcaciones = total
                if primer_ts and (not trabajador.primer_registro or primer_ts < trabajador.primer_registro):
                    trabajador.primer_registro = primer_ts
                if ultimo_ts and (not trabajador.ultimo_registro or ultimo_ts > trabajador.ultimo_registro):
                    trabajador.ultimo_registro = ultimo_ts
            else:
                db.add(
                    Trabajador(
                        user_id=user_id,
                        total_marcaciones=total,
                        primer_registro=primer_ts,
                        ultimo_registro=ultimo_ts,
                        activo=True,
                    )
                )
        db.commit()

    @staticmethod
    def _fase(db, ejecucion: EjecucionSincronizacion, mensaje: str) -> None:
        ejecucion.mensaje_detalle = mensaje
        db.commit()

    @staticmethod
    def _fallar(
        ejecucion_id: int,
        mensaje: str,
        conectado: bool,
        total_leidos: int = 0,
        nuevos: int = 0,
        duplicados: int = 0,
        errores: int = 1,
        duracion: Optional[float] = None,
        modo: Optional[str] = None,
    ) -> None:
        """Registra el fallo en la ejecución y en el dispositivo sin tocar marcaciones."""
        db = SessionLocal()
        try:
            ejecucion = db.get(EjecucionSincronizacion, ejecucion_id)
            if not ejecucion:
                return
            ahora = datetime.utcnow()
            ejecucion.estado = "fallido"
            ejecucion.conexion_ok = conectado
            ejecucion.total_leidos = total_leidos or ejecucion.total_leidos
            ejecucion.nuevos_registros = nuevos or ejecucion.nuevos_registros
            ejecucion.duplicados_omitidos = duplicados or ejecucion.duplicados_omitidos
            ejecucion.errores = errores
            ejecucion.finalizado_el = ahora
            ejecucion.duracion_segundos = (
                duracion
                if duracion is not None
                else round((ahora - ejecucion.iniciado_el).total_seconds(), 2)
            )
            ejecucion.mensaje_detalle = mensaje[:2000]

            dispositivo = (
                db.get(Dispositivo, ejecucion.dispositivo_id)
                if ejecucion.dispositivo_id
                else None
            )
            if dispositivo:
                dispositivo.ultimo_error = mensaje[:250]
                dispositivo.ultimo_error_el = ahora
                if modo:
                    dispositivo.ultimo_modo_conexion = modo
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.error("[sync] No se pudo registrar el fallo: %s", exc)
            db.rollback()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Consulta de estado para el dashboard y la UI
    # ------------------------------------------------------------------
    @staticmethod
    def estado(db) -> Dict[str, Any]:
        SyncService.marcar_ejecuciones_colgadas(db)

        dispositivo = ImportService.get_or_create_default_device(db)
        activa = SyncService._ejecucion_activa(db)

        ultima = (
            db.query(EjecucionSincronizacion)
            .filter(EjecucionSincronizacion.origen == "biometrico_k20")
            .order_by(EjecucionSincronizacion.id.desc())
            .first()
        )
        ultima_completada = (
            db.query(EjecucionSincronizacion)
            .filter(
                EjecucionSincronizacion.origen == "biometrico_k20",
                EjecucionSincronizacion.estado == "completado",
            )
            .order_by(EjecucionSincronizacion.id.desc())
            .first()
        )

        if dispositivo.ultima_conexion_ok and (
            not dispositivo.ultimo_error_el
            or dispositivo.ultima_conexion_ok >= dispositivo.ultimo_error_el
        ):
            estado_conexion = "comprobada"
        elif dispositivo.ultimo_error_el:
            estado_conexion = "sin_conexion"
        else:
            estado_conexion = "configurado"

        return {
            "dispositivo": {
                "id": dispositivo.id,
                "nombre": dispositivo.nombre,
                "ip": dispositivo.ip,
                "puerto": dispositivo.puerto,
                "plataforma": dispositivo.plataforma,
                "modelo": dispositivo.modelo,
                "configurado": True,
                "ultima_conexion_ok": dispositivo.ultima_conexion_ok,
                "ultimo_sync": dispositivo.ultimo_sync,
                "ultimo_error": dispositivo.ultimo_error,
                "ultimo_error_el": dispositivo.ultimo_error_el,
                "ultimo_modo_conexion": dispositivo.ultimo_modo_conexion,
            },
            "estado_conexion": estado_conexion,
            "en_progreso": bool(activa),
            "ejecucion_actual": _ejecucion_dict(activa),
            "ultima_ejecucion": _ejecucion_dict(ultima),
            "ultima_sincronizacion_completada": _ejecucion_dict(ultima_completada),
            "sincronizacion_automatica": {
                "habilitada": settings.SYNC_AUTOMATICA_ENABLED,
                "intervalo_minutos": settings.SYNC_INTERVALO_MINUTOS,
            },
        }

    # ------------------------------------------------------------------
    # Prueba de conexión manual (solo lectura)
    # ------------------------------------------------------------------
    @staticmethod
    def probar_conexion(db) -> Dict[str, Any]:
        dispositivo = ImportService.get_or_create_default_device(db)
        resultado = BiometricoService().probar_conexion(leer_marcaciones=False)
        ahora = datetime.utcnow()
        if resultado["conexion_ok"]:
            dispositivo.ultima_conexion_ok = ahora
            dispositivo.ultimo_error = None
            dispositivo.ultimo_error_el = None
            dispositivo.ultimo_modo_conexion = "prueba"
        else:
            dispositivo.ultimo_error = resultado["mensaje"][:250]
            dispositivo.ultimo_error_el = ahora
            dispositivo.ultimo_modo_conexion = "prueba"
        db.commit()
        return resultado


def _ejecucion_dict(ejecucion: Optional[EjecucionSincronizacion]) -> Optional[Dict[str, Any]]:
    if not ejecucion:
        return None
    return {
        "id": ejecucion.id,
        "origen": ejecucion.origen,
        "modo": ejecucion.modo,
        "estado": ejecucion.estado,
        "conexion_ok": ejecucion.conexion_ok,
        "total_leidos": ejecucion.total_leidos or 0,
        "nuevos_registros": ejecucion.nuevos_registros or 0,
        "duplicados_omitidos": ejecucion.duplicados_omitidos or 0,
        "fechas_sospechosas_detectadas": ejecucion.fechas_sospechosas_detectadas or 0,
        "errores": ejecucion.errores or 0,
        "duracion_segundos": ejecucion.duracion_segundos,
        "ultima_marcacion": ejecucion.ultima_marcacion,
        "mensaje_detalle": ejecucion.mensaje_detalle,
        "iniciado_el": ejecucion.iniciado_el,
        "finalizado_el": ejecucion.finalizado_el,
    }
