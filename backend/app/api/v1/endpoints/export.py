from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marcacion import MarcacionFilterParams
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/excel")
def export_excel(
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    punch: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    fecha_sospechosa: Optional[bool] = Query(None),
    order_by: str = Query("timestamp", description="Campo de orden"),
    order_dir: str = Query("desc", description="Dirección: asc o desc"),
    db: Session = Depends(get_db),
):
    """
    Exporta registros de marcación a archivo Excel (.xlsx) formateado,
    respetando todos los filtros y el orden aplicados.
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

    excel_stream = ExportService.export_to_excel(db, filters)
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"marcaciones_k20_{timestamp_filename}.xlsx"

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )


@router.get("/csv")
def export_csv(
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    punch: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    fecha_sospechosa: Optional[bool] = Query(None),
    order_by: str = Query("timestamp", description="Campo de orden"),
    order_dir: str = Query("desc", description="Dirección: asc o desc"),
    db: Session = Depends(get_db),
):
    """
    Exporta registros de marcación a archivo CSV con codificación UTF-8 BOM,
    respetando todos los filtros y el orden aplicados.
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

    csv_stream = ExportService.export_to_csv_stream(db, filters)
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"marcaciones_k20_{timestamp_filename}.csv"

    return StreamingResponse(
        csv_stream,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )

