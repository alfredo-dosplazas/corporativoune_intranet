import contextlib
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
import win32wnet
import win32netcon
import pywintypes

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def smb_session(username, password, domain="."):
    """
    Context manager dedicado a PROYECTOS_ROOT que utiliza la API nativa de Windows
    (WNetAddConnection2) para conectar a la raíz del recurso compartido remoto
    usando las credenciales de Active Directory del usuario de forma segura.
    """
    root_path_str = str(getattr(settings, "PROYECTOS_ROOT", ""))

    if not root_path_str:
        raise PermissionDenied("La ruta PROYECTOS_ROOT no está configurada en los ajustes del sistema.")

    # Extraer estrictamente la raíz del recurso compartido (ej: \\servidor\recurso)
    limpio = root_path_str.replace("/", "\\").strip()
    if limpio.startswith("\\\\"):
        partes = [p for p in limpio.split("\\") if p]
        if len(partes) >= 2:
            remote_root = f"\\\\{partes[0]}\\{partes[1]}"
        else:
            remote_root = limpio
    else:
        remote_root = limpio

    # Normalizar formato UPN o Dominio\Usuario
    if domain and domain != "." and "@" not in username and "\\" not in username:
        user_full = f"{username}@{domain}"
    elif "\\" in username:
        user_full = username
    else:
        user_full = username

    conexion_exitosa = False

    try:
        # Intento directo de conexión
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
        logger.warning(
            f"Advertencia de red para {user_full} en {remote_root} (Código: {error_code}). Reintentando tras limpieza...")

        # Si hay conflicto o la sesión está en uso (1219, 85, 2250, etc.)
        try:
            # Forzar el cierre de cualquier sesión colgada previa
            win32wnet.WNetCancelConnection2(remote_root, 0, True)

            # Pequeña pausa para permitir que el Administrador de Red de Windows libere el recurso
            import time
            time.sleep(0.1)

            # Reintentar conexión limpia
            win32wnet.WNetAddConnection2(
                win32netcon.RESOURCETYPE_DISK,
                None,
                remote_root,
                None,
                user_full,
                password
            )
            conexion_exitosa = True

        except pywintypes.error as inner_e:
            inner_code = inner_e.winerror
            logger.error(f"Fallo definitivo de conexión SMB para {user_full}. Código Windows: {inner_code}")

            if inner_code == 1326:
                raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
            elif inner_code == 1909:
                raise PermissionDenied("La cuenta de Active Directory se encuentra bloqueada.")
            else:
                raise PermissionDenied(
                    "Conflicto de sesión en el servidor de red. Es posible que otra solicitud esté usando el recurso simultáneamente.")
        except Exception as general_err:
            raise PermissionDenied(f"Error de acceso al recurso de red: {str(general_err)}")

    try:
        yield
    finally:
        # Ceder la conexión al salir del bloque
        if conexion_exitosa:
            with contextlib.suppress(Exception):
                win32wnet.WNetCancelConnection2(remote_root, 0, False)