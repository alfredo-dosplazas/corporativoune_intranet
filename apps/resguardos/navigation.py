def build_resguardos_menu():
    return [
        {
            'key': 'resguardos_equipos',
            'icon': 'icon-[tabler--devices]',
            'title': 'Equipos',
            'url_name': 'resguardos:equipos__list',
            'perms': ['resguardos.view_equipo'],
            'active_patterns': ['equipos__'],
        },
        {
            'key': 'resguardos_documentos',
            'icon': 'icon-[tabler--file-text]',
            'title': 'Resguardos',
            'url_name': 'resguardos:list',
            'perms': ['resguardos.view_resguardo'],
            'active_patterns': ['resguardos__'],
        },
    ]