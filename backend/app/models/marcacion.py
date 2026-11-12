from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, foreign
from app.core.database import Base


class Marcacion(Base):
    __tablename__ = "marcaciones"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # Campo original de reloj / archivo, no se asume como identificador universal único
    uid = Column(Integer, nullable=True, index=True)
    
    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), nullable=True, index=True)
    ejecucion_id = Column(Integer, ForeignKey("ejecuciones_sincronizacion.id"), nullable=True, index=True)
    
    # user_id como texto para mantener ceros a la izquierda
    user_id = Column(String(50), nullable=False, index=True)
    
    # Momento exacto de la marcación
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Valores numéricos originales sin suponer interpretación arbitraria
    status = Column(Integer, nullable=False)
    punch = Column(Integer, nullable=False, index=True)
    
    # Detección de fechas sospechosas / futuras sin alterar datos originales
    fecha_sospechosa = Column(Boolean, nullable=False, default=False, index=True)
    motivo_sospecha = Column(String(100), nullable=True)
    
    # Hash único de deduplicación para inserciones idempotentes y detección de colisiones
    hash_deduplicacion = Column(String(64), unique=True, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    dispositivo = relationship("Dispositivo", back_populates="marcaciones")
    ejecucion = relationship("EjecucionSincronizacion", back_populates="marcaciones")
    trabajador = relationship(
        "Trabajador",
        primaryjoin="foreign(Marcacion.user_id) == Trabajador.user_id",
        back_populates="marcaciones",
        uselist=False,
        lazy="joined",
    )

    @property
    def nombre_trabajador(self) -> str:
        if self.trabajador and self.trabajador.nombre and self.trabajador.nombre.strip():
            return self.trabajador.nombre.strip()
        return "Sin nombre registrado"

    @property
    def departamento_trabajador(self) -> str:
        if self.trabajador and self.trabajador.departamento and self.trabajador.departamento.strip():
            return self.trabajador.departamento.strip()
        return "-"

    # Índices optimizados para reportes y filtros
    __table_args__ = (
        Index("idx_marcaciones_user_ts", "user_id", "timestamp"),
        Index("idx_marcaciones_ts_punch", "timestamp", "punch"),
        Index("idx_marcaciones_ts_sospechosa", "timestamp", "fecha_sospechosa"),
    )

