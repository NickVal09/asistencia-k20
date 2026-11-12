from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class EjecucionSincronizacion(Base):
    __tablename__ = "ejecuciones_sincronizacion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    origen = Column(String(50), nullable=False, default="csv_import")  # 'csv_import', 'biometrico_k20'
    modo = Column(String(20), nullable=True, default="manual")  # 'manual', 'automatico'
    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), nullable=True)
    archivo_nombre = Column(String(255), nullable=True)
    estado = Column(String(30), nullable=False, default="en_progreso")  # 'completado', 'fallido', 'en_progreso', 'interrumpido'
    total_leidos = Column(Integer, default=0, nullable=False)
    nuevos_registros = Column(Integer, default=0, nullable=False)
    duplicados_omitidos = Column(Integer, default=0, nullable=False)
    fechas_sospechosas_detectadas = Column(Integer, default=0, nullable=False)
    errores = Column(Integer, default=0, nullable=False)
    conexion_ok = Column(Boolean, nullable=True)
    duracion_segundos = Column(Float, nullable=True)
    ultima_marcacion = Column(DateTime, nullable=True)
    mensaje_detalle = Column(Text, nullable=True)
    iniciado_el = Column(DateTime, default=datetime.utcnow, nullable=False)
    finalizado_el = Column(DateTime, nullable=True)

    # Relationships
    dispositivo = relationship("Dispositivo", back_populates="ejecuciones")
    marcaciones = relationship("Marcacion", back_populates="ejecucion")

