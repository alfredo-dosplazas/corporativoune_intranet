def build_interfaz_sae_coi_menu():
    return [
        {
            'key': 'documentos_list',
            'icon': 'icon-[fluent--book-contacts-28-filled]',
            'title': 'Documentos',
            'url_name': 'interfaz_sae_coi:documentos_list',
            'perms': ['interfaz_sae_coi.view_documentos'],
            'active_patterns': ['interfaz_sae_coi:'],
        },
    ]
