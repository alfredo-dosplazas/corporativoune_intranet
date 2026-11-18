def get_catalogo_table_name(base_name: str, numero_empresa: str) -> str:
    """
    Genera el nombre de una tabla de catálogo para una empresa (Ej: PUESTOS + 01 -> PUESTOS01).
    """
    return f"{base_name.upper()}{numero_empresa}"


def get_periodo_table_name(prefijo: str, periodo_str: str, numero_empresa: str) -> str:
    """
    Genera el nombre de una tabla histórica por periodo (Ej: TB + 010126 + 01 -> TB01012601).
    """
    return f"{prefijo.upper()}{periodo_str}{numero_empresa}"
