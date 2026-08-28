def build_interfaz_sae_coi_menu():
    return [
        {
            'key': 'documentos_list_inertia',
            'icon': 'icon-[fluent--book-contacts-28-filled]',
            'title': 'Documentos',
            'url_name': 'interfaz_sae_coi:documentos_list_inertia',
            'perms': ['interfaz_sae_coi.view_documentos'],
            'active_patterns': ['interfaz_sae_coi:'],
        },
        {
            'key': 'asignar_cuentas',
            'icon': 'icon-[fluent--book-contacts-28-filled]',
            'title': 'Asignar Cuentas',
            'url_name': 'interfaz_sae_coi:asignar_cuentas',
            'perms': ['interfaz_sae_coi.update_cuenta'],
            'active_patterns': ['interfaz_sae_coi:'],
        }
    ]
