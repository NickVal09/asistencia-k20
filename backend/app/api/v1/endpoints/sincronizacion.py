from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ejecucion import EjecucionSincronizacion
from app.schemas.sincronizacion import (
    EstadoSincronizacion,
    EjecucionSyncInfo,
    PruebaConexionResult,
    SincronizacionInicio,
)
from app.services.sync_service import SyncService

router = APIRouter()


@router.post("/k20", response_model=SincronizacionInicio)
def iniciar_sincronizacion_k20(db: Session = Depends(get_db)):
    """
    Inicia una sincronización manual con el K20 en segundo plano.
    Responde de inmediato; el progreso se consulta en /sincronizacion/estado.
    """
    return SyncService.iniciar_manual(db)


@router.get("/estado", response_model=EstadoSincronizacion)
def estado_sincronizacion(db: Session = Depends(get_db)):
    """Estado real de conexión, ejecución en curso y última sincronización."""
    return SyncService.estado(db)


@router.post("/probar-conexion", response_model=PruebaConexionResult)
def probar_conexion_k20(db: Session = Depends(get_db)):
    """
    Comprueba la conexión con el K20 (solo lectura, sin descargar marcaciones).
    Actualiza la hora de última conexión correcta o el último error.
    """
    return SyncService.probar_conexion(db)


@router.get("/historial", response_model=List[EjecucionSyncInfo])
def historial_sincronizaciones(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historial de sincronizaciones con el biométrico (más recientes primero)."""
    filas = (
        db.query(EjecucionSincronizacion)
        .filter(EjecucionSincronizacion.origen == "biometrico_k20")
        .order_by(desc(EjecucionSincronizacion.id))
        .limit(limit)
        .all()
    )
    return [
        EjecucionSyncInfo(
            id=f.id,
            origen=f.origen,
            modo=f.modo,
            estado=f.estado,
            conexion_ok=f.conexion_ok,
            total_leidos=f.total_leidos or 0,
            nuevos_registros=f.nuevos_registros or 0,
            duplicados_omitidos=f.duplicados_omitidos or 0,
            fechas_sospechosas_detectadas=f.fechas_sospechosas_detectadas or 0,
            errores=f.errores or 0,
            duracion_segundos=f.duracion_segundos,
            ultima_marcacion=f.ultima_marcacion,
            mensaje_detalle=f.mensaje_detalle,
            iniciado_el=f.iniciado_el,
            finalizado_el=f.finalizado_el,
        )
        for f in filas
    ]
