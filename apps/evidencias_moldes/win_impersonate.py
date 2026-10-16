import contextlib
import logging
import ctypes
from django.conf import settings
from django.core.exceptions import PermissionDenied
import win32security
import win32wnet
import win32netcon
import pywintypes

logger = logging.getLogger(__name__)

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32


def validar_credenciales_ad(username, password, domain="."):
    if settings.DEBUG:
        logger.info(f"[DEV] Omitiendo validación AD para {domain}\\{username} (DEBUG=True)")
        return

    # Normalizar formato UPN (usuario@dominio.com) o Dominio\Usuario
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
    """
    Context manager que valida las credenciales y establece una conexión de red
    explícita (equivalente a net use) para que el hilo acceda al recurso remoto.
    """
    if settings.DEBUG:
        logger.info(f"[DEV] Omitiendo impersonación AD para {username} (DEBUG=True)")
        yield
        return

    # 1. Validar que las credenciales sean correctas ante el AD
    validar_credenciales_ad(username, password, domain)

    # 2. Formatear el usuario completo para la red
    if domain and domain != "." and "@" not in username and "\\" not in username:
        user_full = f"{username}@{domain}"
    elif "\\" in username:
        user_full = username
    else:
        user_full = username

    # Obtener la ruta raíz configurada (ej: \\dac-remoto.frescopack.local\compartido)
    remote_root = str(settings.FP_SERVER_ROOT)

    # 3. Conexión de red explícita (Equivalente a net use temporal)
    # Esto evita el error 1219 de sesiones múltiples reutilizando o abriendo un canal autenticado limpio.
    conexion_exitosa = False
    try:
        win32wnet.WNetAddConnection2(
            win32netcon.RESOURCETYPE_DISK,
            None,  # No mapeamos letra de unidad local (usamos UNC directo)
            remote_root,  # Recurso compartido de red
            None,  # Contraseña (va integrada en el bloque de credenciales abajo)
            user_full,  # Usuario con formato UPN o DOMINIO\usuario
            password  # Password
        )
        conexion_exitosa = True
    except pywintypes.error as e:
        # Si el error es 1219 (ya conectado con otro usuario), intentamos desconectar y reconectar
        if e.winerror == 1219:
            try:
                win32wnet.WNetCancelConnection2(remote_root, 0, True)
                win32wnet.WNetAddConnection2(
                    win32netcon.RESOURCETYPE_DISK,
                    None,
                    remote_root,
                    None,
                    user_full,
                    password
                )
                conexion_exitosa = True
            except Exception as inner_e:
                logger.error(f"No se pudo restablecer la conexión de red: {inner_e}")
                raise PermissionError("Conflicto de sesión de red en el servidor.")
        else:
            logger.error(f"Error al conectar recurso de red WNetAddConnection2: {e}")
            raise PermissionError(f"No se pudo autenticar en el recurso de red (Código: {e.winerror})")

    try:
        # Cede el control a la vista de Django para listar/leer archivos
        yield
    finally:
        # 4. Limpieza de la conexión de red al terminar el bloque
        if conexion_exitosa:
            try:
                win32wnet.WNetCancelConnection2(remote_root, 0, True)
            except Exception:
                pass