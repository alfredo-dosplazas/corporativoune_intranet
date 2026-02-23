import os
import time
import shutil
import tempfile
from pathlib import Path

# ==============================
# CONFIGURACIÓN
# ==============================

RUTA_BASE = Path(r"\\172.17.2.201\compartidoCetnet")
RUTA_FINAL = RUTA_BASE / "transacciones.txt"

REINTENTOS = 5
DELAY_REINTENTO = 1  # segundos


# ==============================
# FORMATO DE LÍNEA
# ==============================

def generar_linea_cetnet(r):
    fecha = r["datetime"].strftime("%Y%m%d")
    hora = r["datetime"].strftime("%H%M%S")

    return (
        f"{r['terminal']},"
        f"{fecha},"
        f"{hora},"
        f"{r['source']},"
        f"{r['badge']},"
        f"?,40,40,40,40,40"
    )


# ==============================
# EXPORTACIÓN SEGURA
# ==============================

def exportar_a_archivo(transacciones):
    """
    Exporta transacciones a archivo en recurso compartido de red
    de forma segura y tolerante a bloqueos.
    """

    if not transacciones:
        return 0

    if not RUTA_BASE.exists():
        raise RuntimeError(f"No existe la ruta de red: {RUTA_BASE}")

    # Generar contenido
    lineas = [generar_linea_cetnet(r) for r in transacciones]
    contenido = "\r\n".join(lineas)  # CRLF obligatorio en Windows legacy

    # Crear archivo temporal local (más seguro que crear temp en red)
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        encoding="ascii",
        newline=""
    ) as tmp:
        tmp.write(contenido)
        temp_local_path = Path(tmp.name)

    # Intentar mover al recurso compartido con reintentos
    for intento in range(1, REINTENTOS + 1):
        try:
            # Si existe archivo final, intentar eliminarlo primero
            if RUTA_FINAL.exists():
                try:
                    os.remove(RUTA_FINAL)
                except PermissionError:
                    # Puede estar bloqueado por Cetnet
                    raise

            # Mover archivo (más compatible que os.replace en UNC)
            shutil.move(str(temp_local_path), str(RUTA_FINAL))

            return len(lineas)

        except PermissionError as e:
            if intento == REINTENTOS:
                raise RuntimeError(
                    f"No se pudo reemplazar el archivo después de "
                    f"{REINTENTOS} intentos. Posiblemente está en uso."
                ) from e

            time.sleep(DELAY_REINTENTO)

        except OSError as e:
            if intento == REINTENTOS:
                raise RuntimeError(
                    f"Error de sistema al exportar archivo: {e}"
                ) from e

            time.sleep(DELAY_REINTENTO)

    return 0