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