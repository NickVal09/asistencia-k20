from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DispositivoBase(BaseModel):
    nombre: str
    ip: str
    puerto: int
    plataforma: str
    modelo: str
    activo: bool
    descripcion: Optional[str] = None


class DispositivoRead(DispositivoBase):
    id: int
    ultimo_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DispositivoStatus(BaseModel):
    conectado: bool
    estado: str = "configurado"
    mensaje: str
    detalles: Optional[dict] = None

