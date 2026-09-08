def obtener_cuenta_clave(cuenta_str: str) -> str:
    """
    Ejemplos:
    '1150-001-001-000-000' -> '115000100100000000003' (Nivel 3)
    '1150-001-000-000-000' -> '115000100000000000002' (Nivel 2)
    '1150-000-000-000-000' -> '115000000000000000001' (Nivel 1)
    """
    if not cuenta_str:
        return ""

    # 1. Separar segmentos
    segmentos = [seg.strip() for seg in cuenta_str.split('-')]

    # 2. Calcular el nivel contando los segmentos activos (distintos de cero)
    nivel = 0
    for seg in segmentos:
        # Convertimos a entero para saber si es > 0 (ej. '001' -> 1, '000' -> 0)
        try:
            if int(seg) > 0:
                nivel += 1
        except ValueError:
            pass

    # 3. Quitar guiones a la cuenta original
    cuenta_limpia = cuenta_str.replace('-', '').strip()

    # 4. Formatear el nivel a 5 dígitos (ej. 3 -> '00003')
    nivel_formatted = str(nivel).zfill(5)

    return f"{cuenta_limpia}{nivel_formatted}"