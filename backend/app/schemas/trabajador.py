from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TrabajadorBase(BaseModel):
    user_id: str
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    activo: bool = True


class TrabajadorRead(TrabajadorBase):
    id: int
    total_marcaciones: int
    primer_registro: Optional[datetime] = None
    ultimo_registro: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedTrabajadores(BaseModel):
    items: List[TrabajadorRead]
    total: int
    page: int
    per_page: int
    total_pages: int

