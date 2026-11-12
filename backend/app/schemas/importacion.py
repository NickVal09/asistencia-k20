from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ImportacionResult(BaseModel):
    ejecucion_id: int
    estado: str
    total_leidos: int
    nuevos_registros: int
    duplicados_omitidos: int
    fechas_sospechosas_detectadas: int
    trabajadores_actualizados: int
    errores: int
    mensaje_detalle: Optional[str] = None
    tiempo_segundos: float


class ImportacionColaboradoresResult(BaseModel):
    ejecucion_id: int
    estado: str
    archivo: str
    total_procesados: int
    trabajadores_creados: int
    trabajadores_actualizados: int
    trabajadores_omitidos: int
    nombres_no_disponibles: int = 0
    codigos_sin_coincidencia: int
    errores: int
    diferencias_detectadas_count: int
    mensaje_detalle: Optional[str] = None
    tiempo_segundos: float


class EjecucionRead(BaseModel):
    id: int
    origen: str
    dispositivo_id: Optional[int] = None
    archivo_nombre: Optional[str] = None
    estado: str
    total_leidos: int
    nuevos_registros: int
    duplicados_omitidos: int
    fechas_sospechosas_detectadas: int
    errores: int
    mensaje_detalle: Optional[str] = None
    iniciado_el: datetime
    finalizado_el: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

