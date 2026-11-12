from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import verify_import_authorization
from app.services.import_service import ImportService
from app.services.colaborador_import_service import ColaboradorImportService
from app.schemas.importacion import ImportacionResult, ImportacionColaboradoresResult, EjecucionRead
from app.models.ejecucion import EjecucionSincronizacion

router = APIRouter()


@router.post("/csv", response_model=ImportacionResult, dependencies=[Depends(verify_import_authorization)])
def trigger_csv_import(
    archivo_csv: Optional[str] = Query(None, description="Ruta opcional al archivo CSV. Si se omite, usa la ruta por defecto."),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el proceso de importación del archivo CSV de marcaciones hacia MySQL.
    Operación idempotente: puede ejecutarse múltiples veces de manera segura.
    Requiere autorización mediante API Key / Bearer Token o entorno de desarrollo local.
    """
    try:
        resultado = ImportService.import_csv(db=db, csv_file_path=archivo_csv)
        return ImportacionResult(**resultado)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la importación: {str(e)}"
        )


@router.post("/colaboradores", response_model=ImportacionColaboradoresResult, dependencies=[Depends(verify_import_authorization)])
def trigger_colaboradores_import(
    archivo_xls: Optional[str] = Query(None, description="Ruta opcional al archivo .xls de colaboradores."),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el importador de colaboradores desde el archivo Excel .xls hacia MySQL.
    - Relaciona los nombres y departamentos con las marcaciones existentes.
    - No elimina ni modifica marcaciones originales.
    - Actualiza trabajadores existentes por su código AC No.
    - Operación idempotente.
    """
    try:
        resultado = ColaboradorImportService.import_from_xls(db=db, xls_file_path=archivo_xls)
        return ImportacionColaboradoresResult(**resultado)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la importación de colaboradores: {str(e)}"
        )


@router.get("/historial", response_model=List[EjecucionRead])
def get_import_history(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Retorna el historial de ejecuciones de importación y sincronización."""
    return db.query(EjecucionSincronizacion).order_by(
        desc(EjecucionSincronizacion.id)
    ).limit(limit).all()

