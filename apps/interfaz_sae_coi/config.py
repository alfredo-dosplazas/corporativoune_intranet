CUENTAS_CONFIG = {
    'CLIENTES_GENERAL': '1150-001-001-000-000',
    'IVA_16_TRASLADADO': '2132-001-001-000-000',
    'COSTO_VENTAS_GENERAL': '5000-001-006-000-000',
    'INVENTARIO_GENERAL': '1161-002-001-000-000',
}

ALMACENES_VENTAS_MAP = {
    'SALAMANCA': '4000-001-001-000-000',
    'CORTAZAR': '4000-001-002-000-000',
    'VALLE': '4000-001-003-000-000',
    'PARTE_RELACIONADA': '4000-002-001-003-000',
    'DEFAULT': '4000-001-001-000-000',
}

PARTES_RELACIONADAS = {
    'ABOCOSA': '1150-002-001-000-000',
    'DOS PLAZAS': '1150-002-002-000-000',
    'EDIFICATIUM': '1150-002-003-000-000',
    'TERBA': '1150-002-006-000-000',
    'FRESCOPACK': '1150-002-008-000-000',
}


def get_cuenta_cliente(nombre_cliente: str, rfc: str = '') -> str:
    """Retorna la cuenta especial si es Parte Relacionada, sino la general."""
    nombre_upper = (nombre_cliente or '').upper()
    for key, cuenta in PARTES_RELACIONADAS.items():
        if key in nombre_upper:
            return cuenta
    return CUENTAS_CONFIG['CLIENTES_GENERAL']


def get_cuenta_ventas(almacen: str, es_parte_relacionada=False) -> str:
    """Retorna la cuenta de ventas según el almacén."""
    if es_parte_relacionada:
        return ALMACENES_VENTAS_MAP.get('PARTE_RELACIONADA', ALMACENES_VENTAS_MAP['DEFAULT'])
    almacen_upper = (almacen or '').strip().upper()
    return ALMACENES_VENTAS_MAP.get(almacen_upper, ALMACENES_VENTAS_MAP['DEFAULT'])
