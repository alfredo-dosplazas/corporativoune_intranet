PARTES_RELACIONADAS = [
    'ABOCOSA',
    'DOS PLAZAS',
    'EDIFICATIUM',
    'TERBA',
    'FRESCOPACK',
]


def es_parte_relacionada(nombre_cliente):
    for pr in PARTES_RELACIONADAS:
        if pr in nombre_cliente:
            return True
    return False
