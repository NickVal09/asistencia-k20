import os
import csv
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.models.dispositivo import Dispositivo
from app.models.trabajador import Trabajador
from app.models.marcacion import Marcacion
from app.models.ejecucion import EjecucionSincronizacion
from app.core.config import settings


class ImportService:
    @staticmethod
    def get_or_create_default_device(db: Session) -> Dispositivo:
        """Obtiene o crea el registro del dispositivo ZKTeco K20 configurado."""
        dispositivo = db.query(Dispositivo).filter(
            Dispositivo.ip == settings.ZK_DEVICE_IP,
            Dispositivo.puerto == settings.ZK_DEVICE_PORT
        ).first()

        if not dispositivo:
            dispositivo = Dispositivo(
                nombre=settings.ZK_DEVICE_NAME,
                ip=settings.ZK_DEVICE_IP,
                puerto=settings.ZK_DEVICE_PORT,
                plataforma=settings.ZK_DEVICE_PLATFORM,
                modelo="K20",
                activo=True,
                descripcion="Reloj biométrico principal ZKTeco K20"
            )
            db.add(dispositivo)
            db.commit()
            db.refresh(dispositivo)
        return dispositivo

    @staticmethod
    def calculate_dedup_hash(dispositivo_id: int, user_id: str, ts_str: str, status: int, punch: int) -> str:
        """
        Calcula un hash SHA-256 criptográfico único para la marcación.
        Estrategia de deduplicación independiente del UID original,
        basada en el evento biométrico real: (dispositivo, usuario, timestamp, status, punch).
        """
        raw_key = f"{dispositivo_id}_{user_id.strip()}_{ts_str.strip()}_{status}_{punch}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def import_csv(
        db: Session,
        csv_file_path: str = None,
        batch_size: int = 2500,
    ) -> Dict[str, Any]:
        """
        Importa registros desde el archivo CSV hacia MySQL con total idempotencia.
        No sobrescribe registros existentes, previene duplicados y detecta fechas sospechosas.
        """
        start_time = time.time()
        
        # Resolver ruta del archivo
        target_path = csv_file_path or settings.CSV_DATA_PATH
        if not os.path.isabs(target_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            target_path = os.path.abspath(os.path.join(base_dir, target_path))

        if not os.path.exists(target_path):
            # Intentar ruta alternativa relativa al proyecto
            alt_path = os.path.abspath(os.path.join("C:/Proyectos/asistencia-k20/datos/registros_k20.csv"))
            if os.path.exists(alt_path):
                target_path = alt_path
            else:
                raise FileNotFoundError(f"No se encontró el archivo CSV en: {target_path}")

        dispositivo = ImportService.get_or_create_default_device(db)
        
        # Registrar inicio de ejecución
        ejecucion = EjecucionSincronizacion(
            origen="csv_import",
            dispositivo_id=dispositivo.id,
            archivo_nombre=os.path.basename(target_path),
            estado="en_progreso",
            iniciado_el=datetime.utcnow(),
        )
        db.add(ejecucion)
        db.commit()
        db.refresh(ejecucion)

        # Pre-cargar hashes existentes en la base de datos para búsqueda O(1) ultra rápida
        existing_hashes: Set[str] = set()
        hash_rows = db.query(Marcacion.hash_deduplicacion).all()
        for (h,) in hash_rows:
            existing_hashes.add(h)

        total_read = 0
        new_records = 0
        duplicates_count = 0
        suspicious_detected = 0
        errors_count = 0
        
        # Para agregación de trabajadores
        worker_stats: Dict[str, Dict[str, Any]] = {}

        current_year = datetime.utcnow().year
        
        records_to_insert: List[Marcacion] = []

        try:
            with open(target_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    total_read += 1
                    try:
                        uid_raw = row.get("uid")
                        uid_val = int(uid_raw) if uid_raw and uid_raw.strip().isdigit() else None
                        
                        # Conservar user_id como texto para preservar ceros a la izquierda
                        user_id = str(row["user_id"]).strip()
                        ts_str = str(row["timestamp"]).strip()
                        status_val = int(row["status"])
                        punch_val = int(row["punch"])
                        
                        parsed_ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Detección de fechas sospechosas (futuras o bandera previa)
                        csv_suspicious = str(row.get("fecha_sospechosa", "0")).strip() == "1"
                        is_future = parsed_ts.year > current_year
                        is_suspicious = csv_suspicious or is_future
                        
                        motivo = None
                        if is_future:
                            motivo = f"fecha_futura_anio_{parsed_ts.year}"
                        elif csv_suspicious:
                            motivo = "marcado_en_archivo_origen"
                        
                        if is_suspicious:
                            suspicious_detected += 1

                        # Deduplicación independiente de UID
                        dedup_hash = ImportService.calculate_dedup_hash(
                            dispositivo.id, user_id, ts_str, status_val, punch_val
                        )

                        # Actualizar estadísticas de trabajadores
                        if user_id not in worker_stats:
                            worker_stats[user_id] = {
                                "min_ts": parsed_ts,
                                "max_ts": parsed_ts,
                                "count": 1,
                            }
                        else:
                            st = worker_stats[user_id]
                            st["count"] += 1
                            if parsed_ts < st["min_ts"]:
                                st["min_ts"] = parsed_ts
                            if not is_future and parsed_ts > st["max_ts"]:
                                st["max_ts"] = parsed_ts

                        if dedup_hash in existing_hashes:
                            duplicates_count += 1
                            continue

                        # Registrar hash para evitar duplicados internos dentro del mismo archivo
                        existing_hashes.add(dedup_hash)

                        marcacion = Marcacion(
                            uid=uid_val,
                            dispositivo_id=dispositivo.id,
                            ejecucion_id=ejecucion.id,
                            user_id=user_id,
                            timestamp=parsed_ts,
                            status=status_val,
                            punch=punch_val,
                            fecha_sospechosa=is_suspicious,
                            motivo_sospecha=motivo,
                            hash_deduplicacion=dedup_hash,
                        )
                        records_to_insert.append(marcacion)
                        new_records += 1

                        if len(records_to_insert) >= batch_size:
                            db.bulk_save_objects(records_to_insert)
                            db.commit()
                            records_to_insert.clear()

                    except Exception as row_err:
                        errors_count += 1
                        continue

                # Guardar registros remanentes
                if records_to_insert:
                    db.bulk_save_objects(records_to_insert)
                    db.commit()
                    records_to_insert.clear()

            # Sincronizar catálogo de trabajadores
            updated_workers_count = 0
            for uid, stats in worker_stats.items():
                trabajador = db.query(Trabajador).filter(Trabajador.user_id == uid).first()
                if not trabajador:
                    trabajador = Trabajador(
                        user_id=uid,
                        total_marcaciones=stats["count"],
                        primer_registro=stats["min_ts"],
                        ultimo_registro=stats["max_ts"],
                        activo=True,
                    )
                    db.add(trabajador)
                else:
                    trabajador.total_marcaciones = stats["count"]
                    if not trabajador.primer_registro or stats["min_ts"] < trabajador.primer_registro:
                        trabajador.primer_registro = stats["min_ts"]
                    if not trabajador.ultimo_registro or stats["max_ts"] > trabajador.ultimo_registro:
                        trabajador.ultimo_registro = stats["max_ts"]
                updated_workers_count += 1

            dispositivo.ultimo_sync = datetime.utcnow()
            db.commit()

            duration = round(time.time() - start_time, 2)
            
            # Completar registro de ejecución
            ejecucion.estado = "completado"
            ejecucion.total_leidos = total_read
            ejecucion.nuevos_registros = new_records
            ejecucion.duplicados_omitidos = duplicates_count
            ejecucion.fechas_sospechosas_detectadas = suspicious_detected
            ejecucion.errores = errors_count
            ejecucion.mensaje_detalle = (
                f"Importación exitosa en {duration}s. "
                f"Leídos: {total_read}, Nuevos: {new_records}, Duplicados: {duplicates_count}, "
                f"Sospechosas: {suspicious_detected}, Trabajadores actualizados: {updated_workers_count}"
            )
            ejecucion.finalizado_el = datetime.utcnow()
            db.commit()

            return {
                "ejecucion_id": ejecucion.id,
                "estado": ejecucion.estado,
                "total_leidos": total_read,
                "nuevos_registros": new_records,
                "duplicados_omitidos": duplicates_count,
                "fechas_sospechosas_detectadas": suspicious_detected,
                "trabajadores_actualizados": updated_workers_count,
                "errores": errors_count,
                "mensaje_detalle": ejecucion.mensaje_detalle,
                "tiempo_segundos": duration,
            }

        except Exception as e:
            db.rollback()
            duration = round(time.time() - start_time, 2)
            ejecucion.estado = "fallido"
            ejecucion.mensaje_detalle = f"Error durante la importación: {str(e)}"
            ejecucion.finalizado_el = datetime.utcnow()
            db.commit()
            raise e

