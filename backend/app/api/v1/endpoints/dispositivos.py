from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dispositivo import Dispositivo
from app.schemas.dispositivo import DispositivoRead, DispositivoStatus
from app.services.import_service import ImportService
from app.services.sync_service import SyncService

router = APIRouter()


@router.get("", response_model=List[DispositivoRead])
def list_dispositivos(db: Session = Depends(get_db)):
    """Lista los dispositivos biométricos registrados en el sistema."""
    ImportService.get_or_create_default_device(db)
    return db.query(Dispositivo).all()


@router.get("/k20/status", response_model=DispositivoStatus)
def get_k20_status(db: Session = Depends(get_db)):
    """
    Estado real del K20: configurado / comprobada / sin conexión.
    No afirma estar conectado solo porque la IP esté configurada.
    """
    estado = SyncService.estado(db)
    disp = estado["dispositivo"]
    conectado = estado["estado_conexion"] == "comprobada"
    mensajes = {
        "comprobada": "Conexión comprobada con el reloj K20.",
        "sin_conexion": "Sin conexión con el reloj K20.",
        "configurado": "Dispositivo configurado; conexión no comprobada.",
    }
    return DispositivoStatus(
        conectado=conectado,
        estado=estado["estado_conexion"],
        mensaje=mensajes.get(estado["estado_conexion"], "Configurado"),
        detalles={
            "ip_configurada": disp["ip"],
            "puerto_configurado": disp["puerto"],
            "plataforma": disp["plataforma"],
            "modelo": disp["modelo"],
            "ultima_conexion_ok": disp["ultima_conexion_ok"],
            "ultimo_error": disp["ultimo_error"],
            "ultimo_error_el": disp["ultimo_error_el"],
            "ultimo_sync": disp["ultimo_sync"],
            "estado_conexion": estado["estado_conexion"],
        },
    )
