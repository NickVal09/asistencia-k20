from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EjecucionSyncInfo(BaseModel):
    id: int
    origen: str
    modo: Optional[str] = None
    estado: str
    conexion_ok: Optional[bool] = None
    total_leidos: int = 0
    nuevos_registros: int = 0
    duplicados_omitidos: int = 0
    fechas_sospechosas_detectadas: int = 0
    errores: int = 0
    duracion_segundos: Optional[float] = None
    ultima_marcacion: Optional[datetime] = None
    mensaje_detalle: Optional[str] = None
    iniciado_el: Optional[datetime] = None
    finalizado_el: Optional[datetime] = None


class DispositivoSyncInfo(BaseModel):
    id: int
    nombre: str
    ip: str
    puerto: int
    plataforma: str
    modelo: str
    configurado: bool = True
    ultima_conexion_ok: Optional[datetime] = None
    ultimo_sync: Optional[datetime] = None
    ultimo_error: Optional[str] = None
    ultimo_error_el: Optional[datetime] = None
    ultimo_modo_conexion: Optional[str] = None


class SyncAutomaticaInfo(BaseModel):
    habilitada: bool
    intervalo_minutos: int


class EstadoSincronizacion(BaseModel):
    dispositivo: DispositivoSyncInfo
    estado_conexion: str  # 'configurado' | 'comprobada' | 'sin_conexion'
    en_progreso: bool
    ejecucion_actual: Optional[EjecucionSyncInfo] = None
    ultima_ejecucion: Optional[EjecucionSyncInfo] = None
    ultima_sincronizacion_completada: Optional[EjecucionSyncInfo] = None
    sincronizacion_automatica: SyncAutomaticaInfo


class SincronizacionInicio(BaseModel):
    iniciado: bool
    motivo: Optional[str] = None
    ejecucion_id: Optional[int] = None
    estado: str
    mensaje: str


class PruebaConexionResult(BaseModel):
    conexion_ok: bool
    mensaje: str
    duracion_segundos: float
    detalles: Optional[dict] = None


class SincronizacionHistorialItem(EjecucionSyncInfo):
    pass


class SincronizacionHistorial(BaseModel):
    items: List[SincronizacionHistorialItem]
