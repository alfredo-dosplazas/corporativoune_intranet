import contextlib
import logging
import ctypes
from django.conf import settings
from django.core.exceptions import PermissionDenied
import win32security
import pywintypes

logger = logging.getLogger(__name__)

LOGON32_LOGON_NEW_CREDENTIALS = 9
LOGON32_PROVIDER_WINNT50 = 3

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32


def validar_credenciales_ad(username, password, domain="."):
    # 1. Bypass para entorno local de desarrollo
    if settings.DEBUG:
        logger.info(f"[DEV] Omitiendo validación AD para {domain}\\{username} (DEBUG=True)")
        return

    # Normalizar formato UPN (usuario@dominio.com)
    if domain and domain != "." and "@" not in username and "\\" not in username:
        user_or_upn = f"{username}@{domain}"
        domain_param = ""
    elif "\\" in username:
        domain_param, user_or_upn = username.split("\\", 1)
    else:
        user_or_upn = username
        domain_param = domain

    try:
        handle = win32security.LogonUser(
            user_or_upn,
            domain_param,
            password,
            win32security.LOGON32_LOGON_NETWORK,
            win32security.LOGON32_PROVIDER_DEFAULT
        )
        handle.Close()
    except pywintypes.error as e:
        error_code = e.winerror
        logger.error(f"Fallo de autenticación AD para {user_or_upn}. Código: {error_code}")

        if error_code == 1326:
            raise PermissionDenied(
                "Las credenciales de Active Directory registradas para tu usuario son incorrectas o vencieron."
            )
        elif error_code == 1909:
            raise PermissionDenied("La cuenta de Active Directory se encuentra bloqueada.")
        else:
            raise PermissionDenied(f"Error de autenticación con Active Directory (Código Windows: {error_code}).")


@contextlib.contextmanager
def impersonate_user(username, password, domain="."):
    # 1. Bypass en entorno de desarrollo local
    if settings.DEBUG:
        logger.info(f"[DEV] Omitiendo impersonación AD para {username} (DEBUG=True)")
        yield
        return

    # 2. En producción ejecuta la impersonación real
    validar_credenciales_ad(username, password, domain)

    token = ctypes.c_void_p()

    if domain and domain != "." and "@" not in username and "\\" not in username:
        user_or_upn = f"{username}@{domain}"
        domain_param = ""
    elif "\\" in username:
        domain_param, user_or_upn = username.split("\\", 1)
    else:
        user_or_upn = username
        domain_param = domain

    success = advapi32.LogonUserW(
        user_or_upn,
        domain_param,
        password,
        LOGON32_LOGON_NEW_CREDENTIALS,
        LOGON32_PROVIDER_WINNT50,
        ctypes.byref(token),
    )

    if not success:
        error_code = ctypes.GetLastError()
        raise PermissionDenied(f"No se pudo crear la sesión de red (Código Windows: {error_code}).")

    try:
        advapi32.ImpersonateLoggedOnUser(token)
        yield
    finally:
        advapi32.RevertToSelf()
        kernel32.CloseHandle(token)