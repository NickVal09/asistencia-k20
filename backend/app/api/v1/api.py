from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    auth,
    dashboard,
    marcaciones,
    trabajadores,
    export,
    importacion,
    dispositivos,
    sincronizacion,
    consulta,
)
from app.core.security import verify_authorization

api_router = APIRouter()

# Ruta pública: login (emite el token)
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Rutas protegidas: datos personales y operaciones administrativas
_protegido = [Depends(verify_authorization)]
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["Dashboard"], dependencies=_protegido
)
api_router.include_router(
    marcaciones.router, prefix="/marcaciones", tags=["Marcaciones"], dependencies=_protegido
)
api_router.include_router(
    trabajadores.router, prefix="/trabajadores", tags=["Trabajadores"], dependencies=_protegido
)
api_router.include_router(
    export.router, prefix="/export", tags=["Exportación"], dependencies=_protegido
)
api_router.include_router(
    importacion.router,
    prefix="/importar",
    tags=["Importación y Sincronización"],
    dependencies=_protegido,
)
api_router.include_router(
    dispositivos.router, prefix="/dispositivos", tags=["Dispositivos"], dependencies=_protegido
)
api_router.include_router(
    sincronizacion.router,
    prefix="/sincronizacion",
    tags=["Sincronización K20"],
    dependencies=_protegido,
)
api_router.include_router(
    consulta.router,
    prefix="/consulta",
    tags=["Consulta DNI (RENIEC)"],
    dependencies=_protegido,
)
