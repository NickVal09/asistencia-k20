from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Dispositivo(Base):
    __tablename__ = "dispositivos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, default="ZKTeco K20")
    ip = Column(String(45), nullable=False, default="192.168.10.69")
    puerto = Column(Integer, nullable=False, default=4370)
    plataforma = Column(String(100), nullable=False, default="ZLM60_TFT")
    modelo = Column(String(50), nullable=False, default="K20")
    activo = Column(Boolean, nullable=False, default=True)
    descripcion = Column(String(255), nullable=True)
    ultimo_sync = Column(DateTime, nullable=True)
    # Estado real de conexion con el dispositivo (Fase 2)
    ultima_conexion_ok = Column(DateTime, nullable=True)
    ultimo_error = Column(String(255), nullable=True)
    ultimo_error_el = Column(DateTime, nullable=True)
    ultimo_modo_conexion = Column(String(20), nullable=True)  # 'manual', 'automatico', 'prueba'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    marcaciones = relationship("Marcacion", back_populates="dispositivo")
    ejecuciones = relationship("EjecucionSincronizacion", back_populates="dispositivo")

