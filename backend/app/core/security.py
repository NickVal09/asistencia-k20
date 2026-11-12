"""
Autenticación y autorización del Sistema de Asistencia K20.

- Tokens Bearer firmados con HMAC-SHA256 usando SECRET_KEY (sin estado en BD).
- Contraseña de administrador desde variables de entorno
  (ADMIN_PASSWORD_HASH preferido; ADMIN_PASSWORD solo para desarrollo).
- X-API-Key para automatizaciones (scripts, monitoreo).
- NO existe ningún permiso implícito por venir de localhost.
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)

# --- Límite simple de intentos de login (en memoria, por IP) ---------------
_intentos_fallidos: Dict[str, deque] = defaultdict(deque)


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _firma(cuerpo: str) -> str:
    return _b64e(
        hmac.new(settings.SECRET_KEY.encode("utf-8"), cuerpo.encode("ascii"), hashlib.sha256).digest()
    )


def create_access_token(username: str, minutos: Optional[int] = None) -> str:
    """Crea un token firmado con vencimiento. Formato: base64(payload).firma"""
    ahora = int(time.time())
    payload = {
        "sub": username,
        "iat": ahora,
        "exp": ahora + int(minutos or settings.TOKEN_EXPIRACION_MINUTOS) * 60,
    }
    cuerpo = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{cuerpo}.{_firma(cuerpo)}"


def verify_access_token(token: str) -> Optional[dict]:
    """Valida firma y vencimiento. Devuelve el payload o None."""
    try:
        cuerpo, firma = token.split(".", 1)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(firma, _firma(cuerpo)):
        return None
    try:
        payload = json.loads(_b64d(cuerpo).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


def verify_password(password: str) -> bool:
    """
    Verifica la contraseña contra ADMIN_PASSWORD_HASH (pbkdf2_sha256) o,
    en desarrollo, contra ADMIN_PASSWORD. Sin credenciales configuradas
    el acceso queda denegado (seguro por defecto).
    """
    if not password:
        return False

    if settings.ADMIN_PASSWORD_HASH:
        try:
            algoritmo, iteraciones, salt_b64, hash_b64 = settings.ADMIN_PASSWORD_HASH.split("$", 3)
            if algoritmo != "pbkdf2_sha256":
                return False
            salt = _b64d(salt_b64)
            esperado = _b64d(hash_b64)
            calculado = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, int(iteraciones)
            )
            return hmac.compare_digest(calculado, esperado)
        except (ValueError, TypeError):
            logger.error("ADMIN_PASSWORD_HASH con formato inválido.")
            return False

    if settings.ADMIN_PASSWORD:
        return hmac.compare_digest(password, settings.ADMIN_PASSWORD)

    return False


def credenciales_configuradas() -> bool:
    return bool(settings.ADMIN_PASSWORD_HASH or settings.ADMIN_PASSWORD)


def _clave_intentos(request: Request, usuario: str) -> str:
    host = request.client.host if request.client else "desconocido"
    return f"{host}|{usuario}"


def comprobar_bloqueo_login(request: Request, usuario: str) -> None:
    clave = _clave_intentos(request, usuario)
    ahora = time.time()
    ventana = _intentos_fallidos[clave]
    while ventana and ahora - ventana[0] > settings.LOGIN_BLOQUEO_MINUTOS * 60:
        ventana.popleft()
    if len(ventana) >= settings.LOGIN_MAX_INTENTOS:
        restante = int(settings.LOGIN_BLOQUEO_MINUTOS * 60 - (ahora - ventana[0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Reintenta en {max(restante, 1)} segundos.",
        )


def registrar_intento_fallido(request: Request, usuario: str) -> None:
    _intentos_fallidos[_clave_intentos(request, usuario)].append(time.time())


def limpiar_intentos(request: Request, usuario: str) -> None:
    _intentos_fallidos.pop(_clave_intentos(request, usuario), None)


def _token_de_peticion(
    api_key: Optional[str], credentials: Optional[HTTPAuthorizationCredentials]
) -> Optional[str]:
    if api_key:
        return api_key
    if credentials and credentials.credentials:
        return credentials.credentials
    return None


def verify_authorization(
    api_key: str = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials = Security(bearer_auth),
) -> bool:
    """
    Autorización real del lado del servidor para endpoints administrativos
    y de datos personales. Acepta X-API-Key de automatización o un Bearer
    token firmado. No hay excepción por localhost.
    """
    token = _token_de_peticion(api_key, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.API_ACCESS_TOKEN and hmac.compare_digest(token, settings.API_ACCESS_TOKEN):
        return True

    payload = verify_access_token(token)
    if payload:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_import_authorization(
    api_key: str = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials = Security(bearer_auth),
) -> bool:
    """Alias retrocompatible para los endpoints de importación."""
    return verify_authorization(api_key=api_key, credentials=credentials)


def usuario_actual(
    credentials: HTTPAuthorizationCredentials = Security(bearer_auth),
) -> Tuple[str, str]:
    """Devuelve (usuario, rol) a partir del Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida.")
    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o expiradas.")
    return str(payload.get("sub", "admin")), "admin"
