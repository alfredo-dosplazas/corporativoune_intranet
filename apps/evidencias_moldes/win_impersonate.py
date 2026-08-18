import ctypes
import contextlib
import logging

logger = logging.getLogger(__name__)

LOGON32_LOGON_NEW_CREDENTIALS = 9
LOGON32_PROVIDER_WINNT50 = 3

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32


@contextlib.contextmanager
def impersonate_user(username, password, domain="."):
    """
    Context Manager que suplanta temporalmente la identidad del usuario en Windows
    para que las operaciones NTFS se registren con su token de propietario.
    """
    token = ctypes.c_void_p()

    # Si el usuario incluye el dominio/IP tipo '172.x.x.x\usuario'
    if "\\" in username:
        domain, username = username.split("\\", 1)

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
        logger.error(
            f"Error al autenticar usuario {username} en Windows. Código: {error_code}"
        )
        yield
        return

    try:
        advapi32.ImpersonateLoggedOnUser(token)
        yield
    finally:
        advapi32.RevertToSelf()
        kernel32.CloseHandle(token)
