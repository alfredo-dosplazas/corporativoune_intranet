from django.urls import reverse, NoReverseMatch


class MenuRegistry:
    def __init__(self):
        self._items = []

    def register(self, item):
        """Registra un ítem principal o sección."""
        self._items.append(item)

    def get_items(self):
        return self._items


# Instancia global del registro
site_menu = MenuRegistry()


def build_default_menu():
    """
    Construye la estructura base del menú.
    Usamos closures o lambdas para 'reverse()' para evitar problemas de
    carga de URLs al arrancar Django.
    """
    return [
        {
            'key': 'mas',
            'icon': 'icon-[tabler--dots-vertical]',
            'title': 'Reportes',
            'children': [
                {
                    'key': 'vs_estatus_financiero_obras',
                    'icon': 'icon-[tabler--chart-bar]',
                    'title': 'Estatus Financiero Obras',
                    'url_name': 'vs_erp:reporte_presupuestos',
                    'perms': ['core.generar_reporte_presupuestos_vs'],
                    'active_patterns': ['vs_erp:'],
                }
            ],
        }
    ]


def build_compras_menu():
    """
    Menú específico para el módulo de Compras.
    Alineado a tus URLs de Proveedores y Órdenes de Compra.
    """
    return [
        {
            'key': 'compras_proveedores',
            'icon': 'icon-[tabler--users]',
            'title': 'Proveedores',
            'url_name': 'compras:proveedores__list',
            'perms': ['compras.view_proveedor'],
            'active_patterns': ['proveedores__'],
        },
        {
            'key': 'compras_ordenes',
            'icon': 'icon-[tabler--file-invoice]',
            'title': 'Órdenes de Compra',
            'url_name': 'compras:ordenes__list',
            'perms': ['compras.view_orden'],
            'active_patterns': ['ordenes__'],
        },
    ]


def build_directorio_menu():
    """
    Menú específico para el módulo de Directorio.
    """
    return [
        {
            'key': 'directorio_list',
            'icon': 'icon-[fluent--book-contacts-28-filled]',
            'title': 'Directorio',
            'url_name': 'directorio:list',
            'perms': ['directorio.view_contacto'],
            'active_patterns': ['directorio:'],
        },
    ]


def build_default_dock():
    return [
        {
            "nombre": "Inicio",
            "icon": "icon-[heroicons--home]",
            "url_name": "home",
            "active_patterns": ["home"],
            "exact": True,
        },
        {
            "nombre": "Directorio",
            "icon": "icon-[tabler--address-book]",
            "url_name": "directorio:list",
            "active_patterns": ["directorio:"],
            "perms": ["directorio.view_contacto"],
        },
        {
            "nombre": "Fotos",
            "icon": "icon-[tabler--camera]",
            "url_name": "fotos:root",
            "active_patterns": ["fotos:"],
        },
        {
            "nombre": "Config",
            "icon": "icon-[mdi--gear]",
            "url_name": "configuracion:index",
            "active_patterns": ["configuracion:"],
        },
    ]


def build_compras_dock():
    return [
        {
            "nombre": "Inicio",
            "icon": "icon-[heroicons--home]",
            "url_name": "home",
            "exact": True,
        },
        {
            "nombre": "Órdenes",
            "icon": "icon-[tabler--file-description]",
            "url_name": "compras:ordenes__list",
            "active_patterns": ["compras:ordenes__"],
            "perms": ["compras.view_orden"],
        },
        {
            "nombre": "Proveedores",
            "icon": "icon-[tabler--building-store]",
            "url_name": "compras:proveedores__list",
            "active_patterns": ["compras:proveedores__"],
            "perms": ["compras.view_proveedor"],
        },
    ]
