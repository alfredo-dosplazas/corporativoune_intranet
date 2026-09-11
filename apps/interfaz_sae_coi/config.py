NOMBRES_CUENTAS = {
    '1150-001-001-000-000': 'CLIENTES NACIONALES GENERAL',
    '1150-002-001-000-000': 'CLIENTES PARTE RELACIONADA - ABOCOSA',
    '1150-002-002-000-000': 'CLIENTES PARTE RELACIONADA - DOS PLAZAS',
    '1150-002-003-000-000': 'CLIENTES PARTE RELACIONADA - EDIFICATIUM',
    '1150-002-006-000-000': 'CLIENTES PARTE RELACIONADA - TERBA',
    '1150-002-008-000-000': 'CLIENTES PARTE RELACIONADA - FRESCOPACK',
    '2132-001-001-000-000': 'IVA PENDIENTE DE TRASLADAR (16%)',
    '2133-001-001-000-000': 'IVA TRASLADADO COBRADO (16%)',
    '5000-001-006-000-000': 'COSTO DE VENTAS GENERAL',
    '1161-002-001-000-000': 'INVENTARIO DE MERCANCÍAS',
    '4000-001-001-000-000': 'VENTAS SALAMANCA (16%)',
    '4000-001-002-000-000': 'VENTAS CORTAZAR (16%)',
    '4000-001-003-000-000': 'VENTAS VALLE DE SANTIAGO (16%)',
    '4000-002-001-003-000': 'VENTAS PARTES RELACIONADAS',
    '1130-001-001-000-000': 'TARJETAS DE CRÉDITO Y DEBITO',
    '1120-001-001-000-000': 'BANCO BAJIO 02910',
    '1110-001-001-000-000': 'EFECTIVO SALAMANCA',
    '1110-001-002-000-000': 'EFECTIVO CORTAZAR',
    '4002-001-000-000-000': 'DESCUENTOS Y DEVOLUCIONES',
}


def get_nombre_cuenta(numero_cuenta: str) -> str:
    """Retorna el nombre descriptivo de la cuenta o un valor por defecto."""
    return NOMBRES_CUENTAS.get(numero_cuenta, 'CUENTA CONTABLE')


CUENTAS_CONFIG = {
    'CLIENTES_GENERAL': '1150-001-001-000-000',
    'IVA_16_TRASLADADO': '2132-001-001-000-000',
    'IVA_16_COBRADO': '2133-001-001-000-000',
    'COSTO_VENTAS_GENERAL': '5000-001-006-000-000',
    'INVENTARIO_GENERAL': '1161-002-001-000-000',
    'TARJETAS_CREDITO_DEBITO': '1130-001-001-000-000',
    'BANCO_BAJIO': '1120-001-001-000-000',
    'EFECTIVO_SALAMANCA': '1110-001-001-000-000',
    'EFECTIVO_CORTAZAR': '1110-001-002-000-000',
    'DESCUENTOS': '4002-001-000-000-000',
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


def get_cuenta_caja_banco(almacen, num_cpto):
    if num_cpto in [23, 24]:  # Tarjetas credito y debito
        return CUENTAS_CONFIG['TARJETAS_CREDITO_DEBITO']
    if num_cpto in [10, 26]:  # Efectivo
        if almacen == 'CEDIS':
            return CUENTAS_CONFIG['EFECTIVO_SALAMANCA']
        elif almacen == 'CORTAZAR':
            return CUENTAS_CONFIG['EFECTIVO_CORTAZAR']
    if num_cpto == 22:  # Transferencia
        pass
    return CUENTAS_CONFIG['BANCO_BAJIO']
