import os
import tempfile
import contextlib
from django.conf import settings
from django.core.exceptions import PermissionDenied
from smb.SMBConnection import SMBConnection


@contextlib.contextmanager
def smb_pysmb_session(username, password, domain="."):
    """
    Gestiona una conexión SMB independiente por hilo usando pysmb,
    con manejo seguro de parámetros NTLMv2 para evitar cierres de socket (Error 10054).
    """
    root_path_str = os.environ.get("PROYECTOS_ROOT", str(getattr(settings, "PROYECTOS_ROOT", "")))
    if not root_path_str:
        raise PermissionDenied("La ruta PROYECTOS_ROOT no está configurada en los ajustes.")

    # Limpiar y normalizar la ruta UNC de forma segura
    limpio = root_path_str.replace("/", "\\").strip()
    partes = [p for p in limpio.split("\\") if p]

    if len(partes) < 2:
        raise PermissionDenied(
            f"La ruta PROYECTOS_ROOT ('{root_path_str}') no tiene un formato UNC válido. Debe ser tipo \\\\servidor\\compartido"
        )

    remote_host = partes[0]  # IP del servidor: 172.17.2.1
    share_name = partes[1]   # Recurso compartido: Direccion Obras

    sub_path_parts = partes[2:]
    base_sub_path = "/".join(sub_path_parts)

    # Normalizar usuario y dominio para Active Directory
    clean_username = username.split("@")[0].split("\\")[-1]
    netbios_domain = domain if domain and domain != "." else "WORKGROUP"

    # Nombres de cliente y servidor para la negociación SMB
    client_name = "django-client"
    server_name = remote_host  # Se puede usar la IP directamente

    # Inicializar conexión con soporte estricto NTLMv2
    conn = SMBConnection(
        clean_username,
        password,
        client_name,
        server_name,
        domain=netbios_domain,
        use_ntlm_v2=True,
        is_direct_tcp=True
    )

    try:
        # Intentar conexión al puerto estándar de SMB directo (445)
        connected = conn.connect(remote_host, 445, timeout=15)
        if not connected:
            raise PermissionDenied("El servidor SMB rechazó la conexión en el puerto 445.")
    except Exception as e:
        error_str = str(e).lower()
        if "1326" in error_str or "logon failure" in error_str or "denied" in error_str:
            raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
        elif "10054" in error_str or "reset" in error_str or "connection" in error_str:
            raise PermissionDenied(
                f"El servidor de red ({remote_host}) cerró la conexión abruptamente (Error 10054). "
                "Verifica que el puerto 445 esté abierto y que el servidor permita conexiones SMB directas."
            )
        raise PermissionDenied(f"Error de red al conectar con el servidor SMB: {str(e)}")

    class SMBClientProxy:
        def __init__(self, connection, share, root_prefix):
            self.conn = connection
            self.share = share
            self.root_prefix = root_prefix

        def _get_full_remote_path(self, rel_path):
            limpio_rel = rel_path.replace("\\", "/").strip("/")
            if self.root_prefix:
                if limpio_rel:
                    return f"{self.root_prefix}/{limpio_rel}"
                return self.root_prefix
            return limpio_rel

        def list_dir(self, rel_path=""):
            target_path = self._get_full_remote_path(rel_path)
            try:
                files = self.conn.listPath(self.share, "/" + target_path)
                return files
            except Exception as e:
                raise PermissionDenied(f"No se pudo listar la carpeta remota: {str(e)}")

        def get_file_stream(self, rel_path):
            target_path = self._get_full_remote_path(rel_path)
            file_obj = tempfile.NamedTemporaryFile(delete=False)
            try:
                self.conn.retrieveFile(self.share, "/" + target_path, file_obj)
                file_obj.close()
                return file_obj.name
            except Exception as e:
                file_obj.close()
                with contextlib.suppress(Exception):
                    os.unlink(file_obj.name)
                raise PermissionDenied(f"No se pudo leer el archivo remoto: {str(e)}")

        def save_file(self, rel_path, uploaded_file_chunks):
            target_path = self._get_full_remote_path(rel_path)
            temp_in = tempfile.NamedTemporaryFile(delete=False)
            try:
                for chunk in uploaded_file_chunks:
                    temp_in.write(chunk)
                temp_in.close()

                with open(temp_in.name, "rb") as f_in:
                    self.conn.storeFile(self.share, "/" + target_path, f_in)
            finally:
                with contextlib.suppress(Exception):
                    if os.path.exists(temp_in.name):
                        os.unlink(temp_in.name)

        def check_exists(self, rel_path):
            target_path = self._get_full_remote_path(rel_path)
            try:
                path_dir, file_name = os.path.split("/" + target_path)
                files = self.conn.listPath(self.share, path_dir or "/")
                return any(f.filename == file_name for f in files)
            except Exception:
                return False

    proxy = SMBClientProxy(conn, share_name, base_sub_path)

    try:
        yield proxy
    finally:
        with contextlib.suppress(Exception):
            conn.close()