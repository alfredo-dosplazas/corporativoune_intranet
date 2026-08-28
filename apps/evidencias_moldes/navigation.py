def build_evidencias_moldes_dock():
    return [
        {
            "nombre": "Inicio",
            "icon": "icon-[heroicons--home]",
            "url_name": "home",
            "active_patterns": ["home"],
            "exact": True,
        },
        {
            "nombre": "Evidencias",
            "icon": "icon-[tabler--address-book]",
            "url_name": "evidencias_moldes:root",
            "active_patterns": ["evidencias-moldes:"],
            "perms": ["evidencias_moldes.acceder_explorador_direccion_obras"],
        },
    ]