from typing import Optional

from pydantic import BaseModel, Field


class ConsultaDNI(BaseModel):
    """Datos normalizados que devuelve la consulta de DNI (RENIEC)."""

    dni: str
    nombre_completo: str
    nombres: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    estado_civil: Optional[str] = None
    mensaje: Optional[str] = None


class TrabajadorUpdate(BaseModel):
    """Campos editables de un trabajador. Solo se actualiza lo enviado."""

    nombre: Optional[str] = Field(None, max_length=150)
    departamento: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None
