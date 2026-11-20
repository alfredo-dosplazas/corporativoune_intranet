import contextlib
import smbclient
from smbprotocol.exceptions import (
    SMBAuthenticationError,
    SMBOSError,
    SMBException,
    AccessDenied,
)
from django.core.exceptions import PermissionDenied
from django.http import Http404


class SMBClienteUsuario:
    def __init__(self, host: str, username: str, password: str, domain: str = ""):
        self.host = host.strip("\\/")
        self.password = password
        if domain and domain != "." and "@" not in username and "\\" not in username:
            self.username = f"{domain}\\{username}"
        else:
            self.username = username

    def _unc(self, ruta_relativa: str) -> str:
        ruta_limpia = ruta_relativa.replace("/", "\\").strip("\\")
        return f"\\\\{self.host}\\{ruta_limpia}" if ruta_limpia else f"\\\\{self.host}"

    def _kwargs(self):
        return {
            "username": self.username,
            "password": self.password,
        }

    @contextlib.contextmanager
    def sesion(self):
        try:
            smbclient.register_session(
                self.host,
                username=self.username,
                password=self.password,
                connection_timeout=15,
            )
            yield self
        except SMBAuthenticationError:
            try:
                smbclient.reset_connection_cache()
            except Exception:
                pass
            raise PermissionDenied(
                "Las credenciales de Active Directory son incorrectas, vencieron o están bloqueadas."
            )
        except AccessDenied:
            raise PermissionDenied(
                "Tu usuario de Active Directory no tiene permisos NTFS/DAC en esta ruta."
            )
        except SMBOSError as e:
            msg = str(e)
            if "STATUS_ACCESS_DENIED" in msg or getattr(e, "ntstatus", None) == 0xC0000022:
                raise PermissionDenied("Acceso denegado por permisos de red de Windows.")
            if "STATUS_OBJECT_NAME_NOT_FOUND" in msg or "STATUS_OBJECT_PATH_NOT_FOUND" in msg:
                raise Http404("La carpeta o archivo solicitado no existe en la red.")
            raise PermissionDenied(f"Error de red SMB: {msg}")
        except SMBException as e:
            # Si hubo falta de créditos (0 credits) o estado corrupto de conexión, limpiamos el pool
            try:
                smbclient.reset_connection_cache()
            except Exception:
                pass
            raise PermissionDenied(f"Error de protocolo SMB: {str(e)}")

    def listar_directorio(self, ruta_relativa: str):
        carpetas, archivos = [], []
        for entry in smbclient.scandir(self._unc(ruta_relativa), **self._kwargs()):
            if entry.name.startswith(".") or entry.name == ".thumbs":
                continue
            if entry.is_dir():
                carpetas.append({"nombre": entry.name, "tipo": "carpeta"})
            elif entry.is_file():
                stat = entry.stat()
                archivos.append({
                    "nombre": entry.name,
                    "tamanio": stat.st_size,
                    "mtime": stat.st_mtime,
                })
        return carpetas, archivos

    def stat_archivo(self, ruta_relativa: str):
        return smbclient.stat(self._unc(ruta_relativa), **self._kwargs())

    def crear_carpeta(self, ruta_relativa: str):
        smbclient.mkdir(self._unc(ruta_relativa), **self._kwargs())

    def guardar_archivo(self, ruta_relativa: str, contenido_bytes: bytes):
        with smbclient.open_file(self._unc(ruta_relativa), mode="wb", **self._kwargs()) as f:
            f.write(contenido_bytes)

    def renombrar(self, ruta_origen: str, ruta_destino: str):
        smbclient.rename(self._unc(ruta_origen), self._unc(ruta_destino), **self._kwargs())

    def eliminar(self, ruta_relativa: str):
        ruta_unc = self._unc(ruta_relativa)
        info = smbclient.stat(ruta_unc, **self._kwargs())
        if info.st_mode & 0o170000 == 0o040000:
            for entry in smbclient.scandir(ruta_unc, **self._kwargs()):
                sub_relativa = f"{ruta_relativa}/{entry.name}".strip("/")
                self.eliminar(sub_relativa)
            smbclient.rmdir(ruta_unc, **self._kwargs())
        else:
            smbclient.remove(ruta_unc, **self._kwargs())

    def abrir_stream(self, ruta_relativa: str):
        return smbclient.open_file(self._unc(ruta_relativa), mode="rb", **self._kwargs())