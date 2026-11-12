from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardOverview

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Retorna el resumen consolidado para el Dashboard:
    - Total de marcaciones
    - Trabajadores identificados
    - Marcaciones del día
    - Fechas sospechosas detectadas
    - Distribución de punches
    - Desglose de fechas sospechosas por año
    - Puntos de actividad reciente
    - Estado de última sincronización
    """
    return DashboardService.get_overview(db)

