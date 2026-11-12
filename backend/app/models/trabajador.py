from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, foreign
from app.core.database import Base


class Trabajador(Base):
    __tablename__ = "trabajadores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Conservar user_id como texto para no perder ceros iniciales
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(150), nullable=True)
    departamento = Column(String(100), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    total_marcaciones = Column(Integer, default=0, nullable=False)
    primer_registro = Column(DateTime, nullable=True)
    ultimo_registro = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación con marcaciones
    marcaciones = relationship(
        "Marcacion",
        primaryjoin="Trabajador.user_id == foreign(Marcacion.user_id)",
        back_populates="trabajador",
        lazy="select",
    )

