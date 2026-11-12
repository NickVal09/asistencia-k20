from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, computed_field


class MarcacionRead(BaseModel):
    id: int
    uid: Optional[int] = None
    user_id: str
    timestamp: datetime
    status: int
    punch: int
    fecha_sospechosa: bool
    motivo_sospecha: Optional[str] = None
    dispositivo_id: Optional[int] = None
    ejecucion_id: Optional[int] = None
    nombre_trabajador: str = "Sin nombre registrado"
    departamento_trabajador: Optional[str] = None

    @computed_field
    @property
    def punch_etiqueta(self) -> str:
        """Etiqueta informativa conservando el código original sin suposiciones no verificadas."""
        etiquetas = {
            0: "Punch 0 (Tipo 0)",
            1: "Punch 1 (Tipo 1)",
            4: "Punch 4 (Tipo 4)",
            5: "Punch 5 (Tipo 5)",
        }
        return etiquetas.get(self.punch, f"Punch {self.punch}")

    model_config = ConfigDict(from_attributes=True)


class MarcacionFilterParams(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    user_id: Optional[str] = None
    punch: Optional[int] = None
    status: Optional[int] = None
    fecha_sospechosa: Optional[bool] = None
    order_by: str = "timestamp"
    order_dir: str = "desc"  # 'asc' o 'desc'


class PaginatedMarcaciones(BaseModel):
    items: List[MarcacionRead]
    total: int
    page: int
    per_page: int
    total_pages: int
    filtros_activos: dict

