from datetime import datetime, date
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.marcacion import Marcacion
from app.models.trabajador import Trabajador
from app.models.ejecucion import EjecucionSincronizacion
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardStats,
    PunchDistributionItem,
    SuspiciousYearItem,
    RecentSyncInfo,
    ActivityPoint,
)


class DashboardService:
    @staticmethod
    def get_overview(db: Session) -> DashboardOverview:
        """Calcula de forma rápida y optimizada todas las estadísticas clave del Dashboard."""
        
        # 1. Cantidad total de marcaciones
        total_marcaciones = db.query(func.count(Marcacion.id)).scalar() or 0

        # 2. Cantidad de trabajadores identificados y con nombre
        trabajadores_count = db.query(func.count(Trabajador.id)).scalar() or 0
        trabajadores_con_nombre = db.query(func.count(Trabajador.id)).filter(
            Trabajador.nombre.isnot(None),
            Trabajador.nombre != ""
        ).scalar() or 0

        # Fechas mínimas y máximas generales
        fechas_rango = db.query(
            func.min(Marcacion.timestamp),
            func.max(Marcacion.timestamp)
        ).first()
        min_ts = fechas_rango[0] if fechas_rango else None
        max_ts = fechas_rango[1] if fechas_rango else None

        # Marcaciones del día (usar la fecha de hoy o la fecha más reciente de datos legítimos si hoy no tiene)
        hoy_str = datetime.utcnow().strftime("%Y-%m-%d")
        marcaciones_hoy = db.query(func.count(Marcacion.id)).filter(
            func.date(Marcacion.timestamp) == hoy_str,
            Marcacion.fecha_sospechosa == False
        ).scalar() or 0

        # Si hoy es 0 porque es histórico previo, buscar la fecha del último día con actividad legítima
        fecha_referencia = hoy_str
        if marcaciones_hoy == 0 and max_ts:
            ultimo_legitimo = db.query(func.max(Marcacion.timestamp)).filter(
                Marcacion.fecha_sospechosa == False
            ).scalar()
            if ultimo_legitimo:
                fecha_referencia = ultimo_legitimo.strftime("%Y-%m-%d")
                marcaciones_hoy = db.query(func.count(Marcacion.id)).filter(
                    func.date(Marcacion.timestamp) == fecha_referencia,
                    Marcacion.fecha_sospechosa == False
                ).scalar() or 0

        # 4. Cantidad de fechas sospechosas
        fechas_sospechosas = db.query(func.count(Marcacion.id)).filter(
            Marcacion.fecha_sospechosa == True
        ).scalar() or 0

        # 5. Distribución de tipos de marcación (punch)
        punch_nombres = {
            0: "Punch 0 (Entrada / Check-In base)",
            1: "Punch 1 (Salida / Check-Out base)",
            4: "Punch 4 (Entrada TE / Break Out)",
            5: "Punch 5 (Salida TE / Break In)",
        }
        punch_counts = db.query(
            Marcacion.punch,
            func.count(Marcacion.id)
        ).group_by(Marcacion.punch).all()

        distribucion_punches: List[PunchDistributionItem] = []
        for p_code, count in punch_counts:
            pct = round((count / total_marcaciones * 100), 2) if total_marcaciones > 0 else 0.0
            distribucion_punches.append(PunchDistributionItem(
                punch=p_code,
                nombre=punch_nombres.get(p_code, f"Punch {p_code}"),
                cantidad=count,
                porcentaje=pct,
            ))
        distribucion_punches.sort(key=lambda x: x.cantidad, reverse=True)

        # 6. Desglose detallado de fechas sospechosas
        suspicious_records = db.query(Marcacion).filter(
            Marcacion.fecha_sospechosa == True
        ).order_by(Marcacion.timestamp.asc()).all()

        suspicious_by_year: Dict[str, List[Marcacion]] = {}
        for r in suspicious_records:
            yr = str(r.timestamp.year)
            if yr not in suspicious_by_year:
                suspicious_by_year[yr] = []
            suspicious_by_year[yr].append(r)

        desglose_sospechosas: List[SuspiciousYearItem] = []
        for yr, items in sorted(suspicious_by_year.items()):
            ejemplos = [
                {
                    "id": it.id,
                    "uid": it.uid,
                    "user_id": it.user_id,
                    "timestamp": it.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "punch": it.punch,
                    "status": it.status,
                    "motivo": it.motivo_sospecha,
                }
                for it in items[:5]
            ]
            desglose_sospechosas.append(SuspiciousYearItem(
                anio=yr,
                cantidad=len(items),
                ejemplos=ejemplos,
            ))

        # 7. Actividad reciente para gráfico de tendencia (últimos 14 días con actividad legítima)
        actividad_points: List[ActivityPoint] = []
        actividad_rows = db.query(
            func.date(Marcacion.timestamp).label("fecha_dia"),
            func.count(Marcacion.id).label("total_dia")
        ).filter(
            Marcacion.fecha_sospechosa == False
        ).group_by(
            func.date(Marcacion.timestamp)
        ).order_by(
            desc("fecha_dia")
        ).limit(14).all()

        for f_dia, c_dia in reversed(actividad_rows):
            actividad_points.append(ActivityPoint(
                fecha=str(f_dia),
                cantidad=c_dia,
            ))

        # 8. Última sincronización / importación
        ultima_ejec = db.query(EjecucionSincronizacion).order_by(
            EjecucionSincronizacion.id.desc()
        ).first()

        last_sync = None
        if ultima_ejec:
            last_sync = RecentSyncInfo(
                id=ultima_ejec.id,
                origen=ultima_ejec.origen,
                estado=ultima_ejec.estado,
                finalizado_el=ultima_ejec.finalizado_el,
                total_leidos=ultima_ejec.total_leidos,
                nuevos_registros=ultima_ejec.nuevos_registros,
            )

        # 9. Estado real del dispositivo K20 (Fase 2)
        from app.services.sync_service import SyncService

        estado_sync = SyncService.estado(db)
        disp = estado_sync["dispositivo"]
        ultima_completada = estado_sync["ultima_sincronizacion_completada"]

        from app.schemas.dashboard import DispositivoEstadoInfo

        estado_disp = DispositivoEstadoInfo(
            estado_conexion=estado_sync["estado_conexion"],
            conectado=estado_sync["estado_conexion"] == "comprobada",
            ultima_conexion_ok=disp["ultima_conexion_ok"],
            ultimo_sync=disp["ultimo_sync"],
            ultimo_error=disp["ultimo_error"],
            ultimo_error_el=disp["ultimo_error_el"],
            sincronizacion_automatica=estado_sync["sincronizacion_automatica"]["habilitada"],
            intervalo_minutos=estado_sync["sincronizacion_automatica"]["intervalo_minutos"],
        )

        ultima_marcacion_valida = None
        if ultima_completada and ultima_completada.get("ultima_marcacion"):
            ultima_marcacion_valida = ultima_completada["ultima_marcacion"]

        return DashboardOverview(
            stats=DashboardStats(
                total_marcaciones=total_marcaciones,
                trabajadores_identificados=trabajadores_count,
                trabajadores_con_nombre=trabajadores_con_nombre,
                marcaciones_hoy=marcaciones_hoy,
                fechas_sospechosas=fechas_sospechosas,
                fecha_maxima_registrada=max_ts,
                fecha_minima_registrada=min_ts,
                fecha_referencia_hoy=fecha_referencia,
            ),
            distribucion_punches=distribucion_punches,
            desglose_sospechosas=desglose_sospechosas,
            actividad_reciente=actividad_points,
            ultima_sincronizacion=last_sync,
            estado_dispositivo=estado_disp,
            ultima_marcacion_valida=ultima_marcacion_valida,
        )

