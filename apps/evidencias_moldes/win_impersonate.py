import ctypes
import contextlib
import logging
from django.core.exceptions import PermissionDenied
import win32security
import pywintypes

logger = logging.getLogger(__name__)

# Valor 9: Permite impersonar credenciales salientes hacia recursos SMB/Red
LOGON32_LOGON_NEW_CREDENTIALS = 9
LOGON32_PROVIDER_WINNT50 = 3

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32


def validar_credenciales_ad(username, password, domain="."):
    """
    Realiza una prueba rápida de autenticación contra el AD.
    Lanza PermissionDenied con mensaje amigable si falla la contraseña o la cuenta.
    """
    if "\\" in username:
        domain, username = username.split("\\", 1)

    try:
        # Intenta autenticar la credencial en la red
        handle = win32security.LogonUser(
            username,
            domain,
            password,
            win32security.LOGON32_LOGON_NETWORK,
            win32security.LOGON32_PROVIDER_DEFAULT
        )
        handle.Close()
    except pywintypes.error as e:
        # e.winerror contiene el código numérico de Windows
        error_code = e.winerror
        logger.error(f"Fallo de autenticación AD para {domain}\\{username}. Código: {error_code}")

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
    # 1. Validar credenciales primero. Si falla, lanzará PermissionDenied y detendrá la ejecución aquí.
    validar_credenciales_ad(username, password, domain)

    token = ctypes.c_void_p()

    if "\\" in username:
        domain, username = username.split("\\", 1)

    # 2. Como ya sabemos que la contraseña es correcta, ejecutamos la impersonación con la constante 9
    success = advapi32.LogonUserW(
        username,
        domain,
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