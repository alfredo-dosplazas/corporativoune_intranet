import hashlib
import logging

from django.conf import settings

import requests

logger = logging.getLogger("monitoreo_servicios.services.pbx")

PBX_HOST = "172.17.1.202"
PBX_PORT = 8088
PBX_USER = settings.PBX_USER
PBX_PASS = settings.PBX_PASSWORD

password_hashed = hashlib.md5(PBX_PASS.encode("utf-8")).hexdigest()
BASE_URL = f"http://{PBX_HOST}:{PBX_PORT}/api"


def login_pbx_api() -> str | None:
    """Obtiene token de autenticación para el PBX"""
    url = f"{BASE_URL}/v1.10/login"
    payload = {
        "username": PBX_USER,
        "password": password_hashed,
        "port": PBX_PORT,
        "version": "2.0.0"
    }

    logger.info("🔐 Autenticando contra PBX")

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        token = r.json().get("token")

        if not token:
            logger.error("❌ Login PBX exitoso pero sin token")
            logger.error(r.json())
            return None

        logger.info("✅ Token PBX obtenido correctamente")
        return token

    except requests.RequestException as e:
        logger.exception("❌ Error autenticando PBX")
        return None


def obtener_estado_extensiones(token: str) -> list:
    url = f"{BASE_URL}/v1.1.0/extensionlist/query"
    params = {"token": token}

    logger.info("📞 Consultando extensiones PBX")

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("extlist", [])
        logger.info("📞 Extensiones obtenidas: %s", len(data))
        return data

    except requests.RequestException:
        logger.exception("❌ Error obteniendo extensiones PBX")
        return []


def obtener_trunks(token: str) -> list:
    url = f"{BASE_URL}/v1.1.0/trunklist/query"
    params = {"token": token}

    logger.info("🌐 Consultando trunks PBX")

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("trunklist", [])
        logger.info("🌐 Trunks obtenidos: %s", len(data))
        return data

    except requests.RequestException:
        logger.exception("❌ Error obteniendo trunks PBX")
        return []


def obtener_estado_pbx() -> dict:
    token = login_pbx_api()
    if not token:
        logger.error("❌ No se pudo obtener estado PBX (sin token)")
        return {
            "extensiones_total": 0,
            "extensiones_desconectadas": 0,
            "trunks_total": 0,
            "trunks_desconectados": 0,
            "lista_extensiones_desconectadas": [],
            "lista_trunks_desconectados": [],
        }

    extensiones = obtener_estado_extensiones(token)
    trunks = obtener_trunks(token)

    extensiones_desconectadas = [
        e for e in extensiones if e.get("status") == "Unavailable"
    ]

    trunks_desconectados = [
        t for t in trunks if t.get("status") != "Idle"
    ]

    resumen = {
        "extensiones_total": len(extensiones),
        "extensiones_desconectadas": len(extensiones_desconectadas),
        "trunks_total": len(trunks),
        "trunks_desconectados": len(trunks_desconectados),
        "lista_extensiones_desconectadas": extensiones_desconectadas,
        "lista_trunks_desconectados": trunks_desconectados,
    }

    logger.info("📊 Resumen PBX generado: %s", resumen)
    return resumen
