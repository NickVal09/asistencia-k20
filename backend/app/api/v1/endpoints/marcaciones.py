from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
import math

from app.core.database import get_db
from app.services.marcacion_service import MarcacionService
from app.schemas.marcacion import MarcacionRead, PaginatedMarcaciones, MarcacionFilterParams
from app.models.marcacion import Marcacion

router = APIRouter()


@router.get("", response_model=PaginatedMarcaciones)
def list_marcaciones(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha y hora inicial"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha y hora final"),
    user_id: Optional[str] = Query(None, description="ID del trabajador (texto exacto o con %)"),
    punch: Optional[int] = Query(None, description="Código de punch (0, 1, 4, 5)"),
    status: Optional[int] = Query(None, description="Código de status del lector"),
    fecha_sospechosa: Optional[bool] = Query(None, description="Filtrar solo sospechosas (true) o normales (false)"),
    order_by: str = Query("timestamp", description="Campo de orden: id, uid, user_id, nombre, departamento, timestamp, status, punch, fecha_sospechosa"),
    order_dir: str = Query("desc", description="Dirección: asc o desc"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=500, description="Registros por página"),
    db: Session = Depends(get_db),
):
    """
    Lista marcaciones con paginación desde el backend y filtros avanzados por:
    - Rango de fechas
    - Identificador de trabajador
    - Tipo / Código punch
    - Estado / Status lector
    - Detección de fechas sospechosas
    """
    filters = MarcacionFilterParams(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        user_id=user_id,
        punch=punch,
        status=status,
        fecha_sospechosa=fecha_sospechosa,
        order_by=order_by,
        order_dir=order_dir,
    )

    items, total = MarcacionService.get_paginated(db, filters, page=page, per_page=per_page)
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedMarcaciones(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filtros_activos={
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "user_id": user_id,
            "punch": punch,
            "status": status,
            "fecha_sospechosa": fecha_sospechosa,
            "order_by": order_by,
            "order_dir": order_dir,
        }
    )


@router.get("/{id}", response_model=MarcacionRead)
def get_marcacion(id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle completo de una marcación específica."""
    marcacion = db.query(Marcacion).filter(Marcacion.id == id).first()
    if not marcacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marcación con ID {id} no encontrada."
        )
    return marcacion

