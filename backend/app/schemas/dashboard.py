from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DispositivoEstadoInfo(BaseModel):
    estado_conexion: str = "configurado"  # 'configurado' | 'comprobada' | 'sin_conexion'
    conectado: bool = False
    ultima_conexion_ok: Optional[datetime] = None
    ultimo_sync: Optional[datetime] = None
    ultimo_error: Optional[str] = None
    ultimo_error_el: Optional[datetime] = None
    sincronizacion_automatica: bool = False
    intervalo_minutos: int = 10


class DashboardStats(BaseModel):
    total_marcaciones: int
    trabajadores_identificados: int
    trabajadores_con_nombre: int = 0
    marcaciones_hoy: int
    fechas_sospechosas: int
    fecha_maxima_registrada: Optional[datetime] = None
    fecha_minima_registrada: Optional[datetime] = None
    fecha_referencia_hoy: str


class PunchDistributionItem(BaseModel):
    punch: int
    nombre: str
    cantidad: int
    porcentaje: float


class SuspiciousYearItem(BaseModel):
    anio: str
    cantidad: int
    ejemplos: List[Dict[str, Any]]


class RecentSyncInfo(BaseModel):
    id: Optional[int] = None
    origen: Optional[str] = None
    estado: Optional[str] = None
    finalizado_el: Optional[datetime] = None
    total_leidos: int = 0
    nuevos_registros: int = 0


class ActivityPoint(BaseModel):
    fecha: str
    cantidad: int


class DashboardOverview(BaseModel):
    stats: DashboardStats
    distribucion_punches: List[PunchDistributionItem]
    desglose_sospechosas: List[SuspiciousYearItem]
    actividad_reciente: List[ActivityPoint]
    ultima_sincronizacion: Optional[RecentSyncInfo] = None
    estado_dispositivo: Optional[DispositivoEstadoInfo] = None
    ultima_marcacion_valida: Optional[datetime] = None

