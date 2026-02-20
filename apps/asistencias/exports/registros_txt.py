import os


RUTA_BASE = r"\\172.17.2.201\compartidoCetnet"
RUTA_FINAL = os.path.join(RUTA_BASE, "transacciones.txt")
RUTA_TEMP = os.path.join(RUTA_BASE, "transacciones.tmp")


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


def exportar_a_archivo(transacciones):

    if not transacciones:
        return 0

    lineas = [generar_linea_cetnet(r) for r in transacciones]
    contenido = "\n".join(lineas)

    with open(RUTA_TEMP, "w", encoding="utf-8") as f:
        f.write(contenido)

    os.replace(RUTA_TEMP, RUTA_FINAL)

    return len(lineas)