import contextlib
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
import win32wnet
import win32netcon
import pywintypes

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def smb_session_user(username, password, domain="."):
    """
    Context manager que utiliza la API nativa de Windows (WNetAddConnection2)
    para conectar al recurso compartido remoto usando las credenciales del usuario de AD.
    """
    # if settings.DEBUG:
    #     logger.info(f"[DEV] Omitiendo SMB AD para {domain}\\{username} (DEBUG=True)")
    #     yield
    #     return

    # Normalizar formato UPN o Dominio\Usuario
    if domain and domain != "." and "@" not in username and "\\" not in username:
        user_full = f"{username}@{domain}"
    elif "\\" in username:
        user_full = username
    else:
        user_full = username

    # Ruta raíz del servidor remoto (ej: \\172.16.2.1 o \\dac-remoto.frescopack.local)
    remote_root = str(settings.FP_SERVER_ROOT)
    conexion_exitosa = False

    try:
        # Abrir la sesión autenticada de red para este hilo de ejecución
        win32wnet.WNetAddConnection2(
            win32netcon.RESOURCETYPE_DISK,
            None,
            remote_root,
            None,
            user_full,
            password
        )
        conexion_exitosa = True

    except pywintypes.error as e:
        error_code = e.winerror
        logger.error(f"Fallo de conexión de red para {user_full}. Código Windows: {error_code}")

        if error_code == 1219:
            # Si hay conflicto de sesión previa en la PC, limpiamos y reintentamos
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
                logger.error(f"Error al reintentar conexión limpia: {inner_e}")
                raise PermissionDenied("Conflicto de sesión en el servidor de red.")
        elif error_code == 1326:
            raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
        elif error_code == 1909:
            raise PermissionDenied("La cuenta de Active Directory se encuentra bloqueada.")
        else:
            raise PermissionDenied(f"Error de acceso al recurso de red (Código Windows: {error_code}).")

    try:
        # Cede el control a la vista de Django para leer/listar con pathlib de manera normal
        yield
    finally:
        # Limpiar y cerrar la conexión de red al terminar la petición HTTP
        if conexion_exitosa:
            try:
                win32wnet.WNetCancelConnection2(remote_root, 0, True)
            except Exception:
                pass