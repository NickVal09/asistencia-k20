from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.security import (
    comprobar_bloqueo_login,
    create_access_token,
    credenciales_configuradas,
    limpiar_intentos,
    registrar_intento_fallido,
    usuario_actual,
    verify_password,
)
from app.schemas.auth import LoginRequest, LoginResponse, UsuarioInfo

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, request: Request):
    """Autentica al administrador y entrega un token Bearer firmado."""
    comprobar_bloqueo_login(request, datos.usuario)

    if not credenciales_configuradas():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No hay credenciales de administrador configuradas. "
                "Define ADMIN_PASSWORD_HASH (o ADMIN_PASSWORD en desarrollo) en backend/.env."
            ),
        )

    password_valida = verify_password(datos.password)
    if datos.usuario != settings.ADMIN_USER or not password_valida:
        registrar_intento_fallido(request, datos.usuario)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )

    limpiar_intentos(request, datos.usuario)
    token = create_access_token(datos.usuario)
    return LoginResponse(
        access_token=token,
        usuario=datos.usuario,
        expira_en_minutos=settings.TOKEN_EXPIRACION_MINUTOS,
    )


@router.get("/me", response_model=UsuarioInfo)
def me(actual=Depends(usuario_actual)):
    """Devuelve el usuario autenticado; sirve para validar el token guardado."""
    usuario, rol = actual
    return UsuarioInfo(usuario=usuario, rol=rol)
