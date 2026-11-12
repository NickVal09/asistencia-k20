"""
Consulta de DNI contra la API de AQPFACT (RENIEC).

El token de AQPFACT vive solo en el servidor (variable de entorno
AQPFACT_API_TOKEN). El frontend nunca lo ve: pide el DNI a este backend y
este hace la llamada externa.
"""

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cloudflare (detrás de apis.aqpfact.pe) bloquea el User-Agent por defecto de
# urllib con "Error 1010: browser_signature_banned". Un UA de navegador normal
# evita ese bloqueo.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def normalizar_dni(dni: str) -> str:
    limpio = re.sub(r"\D", "", str(dni or ""))
    if len(limpio) != 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El DNI debe tener exactamente 8 dígitos.",
        )
    return limpio


def consultar_dni(dni: str) -> dict:
    """Devuelve los datos normalizados del DNI o lanza HTTPException."""
    numero = normalizar_dni(dni)

    if not settings.AQPFACT_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "La consulta de DNI no está configurada. "
                "Defina AQPFACT_API_TOKEN en el servidor."
            ),
        )

    url = f"{settings.AQPFACT_API_URL.rstrip('/')}/dni/{urllib.parse.quote(numero)}"
    peticion = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.AQPFACT_API_TOKEN}",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(peticion, timeout=settings.AQPFACT_TIMEOUT_SEGUNDOS) as respuesta:
            cuerpo = respuesta.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró información para el DNI {numero}.",
            ) from exc
        if exc.code in (401, 403):
            logger.error("AQPFACT rechazó la petición (HTTP %s).", exc.code)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "El servicio de consulta rechazó la petición "
                    "(token inválido o acceso bloqueado)."
                ),
            ) from exc
        logger.error("AQPFACT respondió HTTP %s para el DNI %s.", exc.code, numero)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"El servicio de consulta de DNI respondió con error {exc.code}.",
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.error("No se pudo conectar con AQPFACT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="No se pudo conectar con el servicio de consulta de DNI. Intente nuevamente.",
        ) from exc

    try:
        payload = json.loads(cuerpo)
    except json.JSONDecodeError as exc:
        logger.error("AQPFACT devolvió una respuesta no JSON: %s", cuerpo[:200])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio de consulta de DNI devolvió una respuesta inválida.",
        ) from exc

    if not payload.get("success"):
        mensaje = payload.get("message") or f"No se encontró información para el DNI {numero}."
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=mensaje)

    datos = payload.get("data") or {}
    nombre_completo = (
        datos.get("nombre_completo")
        or datos.get("name")
        or _componer_nombre(datos)
    )
    if not nombre_completo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró información para el DNI {numero}.",
        )

    return {
        "dni": datos.get("numero") or numero,
        "nombre_completo": nombre_completo.strip(),
        "nombres": _limpiar(datos.get("nombres")),
        "apellido_paterno": _limpiar(datos.get("apellido_paterno")),
        "apellido_materno": _limpiar(datos.get("apellido_materno")),
        "fecha_nacimiento": _limpiar(datos.get("fecha_nacimiento")),
        "sexo": _limpiar(datos.get("sexo")),
        "estado_civil": _limpiar(datos.get("estado_civil")),
        "mensaje": payload.get("message"),
    }


def _limpiar(valor) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _componer_nombre(datos: dict) -> str:
    partes = [
        datos.get("nombres"),
        datos.get("apellido_paterno"),
        datos.get("apellido_materno"),
    ]
    return " ".join(str(p).strip() for p in partes if p)
