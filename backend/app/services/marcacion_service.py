from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, or_, case, cast, Integer

from app.models.marcacion import Marcacion
from app.models.trabajador import Trabajador
from app.schemas.marcacion import MarcacionFilterParams


class MarcacionService:
    @staticmethod
    def get_filtered_query(db: Session, filters: MarcacionFilterParams):
        """Construye la consulta base aplicando filtros dinámicos y relación con Trabajador."""
        # Unir con Trabajador mediante OUTER JOIN para asegurar nombres y departamentos
        query = db.query(Marcacion).outerjoin(
            Trabajador, Marcacion.user_id == Trabajador.user_id
        ).options(
            joinedload(Marcacion.trabajador)
        )

        if filters.fecha_inicio:
            query = query.filter(Marcacion.timestamp >= filters.fecha_inicio)

        if filters.fecha_fin:
            query = query.filter(Marcacion.timestamp <= filters.fecha_fin)

        if filters.user_id:
            u_str = filters.user_id.strip()
            # Permite buscar tanto por código exacto/parcial como por nombre del colaborador
            if "%" in u_str:
                query = query.filter(
                    or_(
                        Marcacion.user_id.like(u_str),
                        Trabajador.nombre.like(u_str),
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Marcacion.user_id == u_str,
                        Trabajador.nombre.like(f"%{u_str}%"),
                    )
                )

        if filters.punch is not None:
            query = query.filter(Marcacion.punch == filters.punch)

        if filters.status is not None:
            query = query.filter(Marcacion.status == filters.status)

        if filters.fecha_sospechosa is not None:
            query = query.filter(Marcacion.fecha_sospechosa == filters.fecha_sospechosa)

        return query

    @staticmethod
    def aplicar_orden(query, filters: MarcacionFilterParams):
        """Aplica el orden solicitado (columna y sentido) de forma reutilizable.

        Usado por la consulta paginada y por las exportaciones para que ambas
        respeten el mismo criterio elegido en la interfaz.
        """
        order_col = Marcacion.timestamp
        ordenar_nulos_al_final = False
        if filters.order_by == "user_id":
            # user_id es VARCHAR (para conservar ceros iniciales): se ordena
            # numéricamente para que sea 1, 2, 3, ..., 9, 10 y no 1, 10, 100.
            order_col = cast(Marcacion.user_id, Integer)
        elif filters.order_by == "nombre":
            order_col = Trabajador.nombre
            ordenar_nulos_al_final = True
        elif filters.order_by == "departamento":
            order_col = Trabajador.departamento
            ordenar_nulos_al_final = True
        elif filters.order_by == "punch":
            order_col = Marcacion.punch
        elif filters.order_by == "status":
            order_col = Marcacion.status
        elif filters.order_by == "uid":
            order_col = Marcacion.uid
        elif filters.order_by == "id":
            order_col = Marcacion.id
        elif filters.order_by == "fecha_sospechosa":
            order_col = Marcacion.fecha_sospechosa

        # Los valores vacíos o sin nombre se envían al final en ambos sentidos
        if ordenar_nulos_al_final:
            es_nulo = case((or_(order_col.is_(None), order_col == ""), 1), else_=0)
            query = query.order_by(es_nulo.asc())

        if filters.order_dir.lower() == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))

        # Desempate estable para que la paginación (y la exportación) sea determinista
        return query.order_by(asc(Marcacion.id))

    @staticmethod
    def get_paginated(
        db: Session,
        filters: MarcacionFilterParams,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[Marcacion], int]:
        """Obtiene una página de marcaciones con la relación del trabajador cargada y total exacto."""
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50
        if per_page > 500:
            per_page = 500

        query = MarcacionService.get_filtered_query(db, filters)

        # Total count
        total = query.count()

        query = MarcacionService.aplicar_orden(
            MarcacionService.get_filtered_query(db, filters), filters
        )

        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        return items, total
