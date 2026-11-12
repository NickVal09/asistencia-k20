import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, case, cast, Integer

from app.core.database import get_db
from app.models.trabajador import Trabajador
from app.schemas.trabajador import TrabajadorRead, PaginatedTrabajadores

router = APIRouter()

# Campos permitidos para ordenar el padrón
CAMPOS_ORDEN = {
    "id": Trabajador.id,
    # user_id es VARCHAR (conserva ceros iniciales): se ordena numéricamente.
    "user_id": cast(Trabajador.user_id, Integer),
    "nombre": Trabajador.nombre,
    "departamento": Trabajador.departamento,
    "total_marcaciones": Trabajador.total_marcaciones,
    "primer_registro": Trabajador.primer_registro,
    "ultimo_registro": Trabajador.ultimo_registro,
    "activo": Trabajador.activo,
}


@router.get("", response_model=PaginatedTrabajadores)
def list_trabajadores(
    search: Optional[str] = Query(None, description="Búsqueda por user_id o nombre"),
    order_by: str = Query("total_marcaciones", description="Campo de orden: id, user_id, nombre, departamento, total_marcaciones, primer_registro, ultimo_registro, activo"),
    order_dir: str = Query("desc", description="Dirección: asc o desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista todos los trabajadores identificados a partir de las marcaciones."""
    query = db.query(Trabajador)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Trabajador.user_id.like(s), Trabajador.nombre.like(s)))

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    order_col = CAMPOS_ORDEN.get(order_by, Trabajador.total_marcaciones)

    # Los nombres o departamentos vacíos se envían al final en ambos sentidos
    if order_by in ("nombre", "departamento"):
        es_nulo = case((or_(order_col.is_(None), order_col == ""), 1), else_=0)
        query = query.order_by(es_nulo.asc())

    if order_dir.lower() == "asc":
        query = query.order_by(asc(order_col))
    else:
        query = query.order_by(desc(order_col))

    # Desempate estable para la paginación
    query = query.order_by(asc(Trabajador.id))

    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return PaginatedTrabajadores(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=TrabajadorRead)
def get_trabajador(user_id: str, db: Session = Depends(get_db)):
    """Obtiene los detalles de un trabajador específico por su user_id."""
    trabajador = db.query(Trabajador).filter(Trabajador.user_id == user_id.strip()).first()
    if not trabajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador con ID {user_id} no encontrado."
        )
    return trabajador

