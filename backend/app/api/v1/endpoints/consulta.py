from fastapi import APIRouter

from app.schemas.consulta_dni import ConsultaDNI
from app.services.consulta_dni_service import consultar_dni

router = APIRouter()


@router.get(
    "/dni/{dni}",
    response_model=ConsultaDNI,
    summary="Consultar DNI en RENIEC",
    description=(
        "Busca el nombre de una persona por su DNI usando la API de AQPFACT. "
        "El token nunca se expone al navegador: lo usa solo el servidor."
    ),
)
def consultar_dni_endpoint(dni: str):
    """Proxy autenticado hacia AQPFACT para no exponer el token en el frontend."""
    return consultar_dni(dni)
