from django.urls import NoReverseMatch, reverse

from apps.core.models import Empresa
from apps.core.navigation import build_default_menu, build_compras_menu
from apps.core.utils.network import get_client_ip, get_empresa_from_ip


def empresas(request):
    context = {
        'empresas': Empresa.objects.all(),
    }

    return context


def empresa(request):
    if request.user.is_authenticated:
        empresa = getattr(getattr(request.user, 'contacto', None), 'empresa', None)
    else:
        ip = get_client_ip(request)
        empresa = get_empresa_from_ip(ip)

    if empresa is None:
        empresa = Empresa.objects.get(nombre_corto='Dos Plazas')

    context = {
        'empresa': empresa
    }

    return context


def process_menu_items(items, request):
    result = []
    current_url_name = request.resolver_match.view_name if request.resolver_match else ''
    current_namespace = request.resolver_match.namespace if request.resolver_match else ''

    for item in items:
        # 1. Control de Permisos
        perms = item.get('perms', [])
        if perms and not request.user.has_perms(perms):
            continue

        # Evitar mutar el diccionario original
        item_copy = item.copy()

        # 2. Resolver URL
        if 'url_name' in item_copy:
            try:
                item_copy['url'] = reverse(item_copy['url_name'])
            except NoReverseMatch:
                item_copy['url'] = '#'
        else:
            item_copy['url'] = item_copy.get('url', '#')

        # 3. Procesar Hijos (Submenús) recursivamente
        has_active_child = False
        if 'children' in item_copy:
            item_copy['children'] = process_menu_items(item_copy['children'], request)
            # Si no quedan hijos visibles por permisos, descartamos el padre o lo ocultamos
            if not item_copy['children']:
                continue

            # Si algún hijo está activo, marcamos al padre como activo
            has_active_child = any(child.get('active', False) for child in item_copy['children'])

        # 4. Determinar si está Activo
        item_copy['active'] = has_active_child or is_item_active(
            item_copy,
            request.path,
            current_url_name,
            current_namespace
        )

        result.append(item_copy)

    return result


def is_item_active(item, current_path, current_url_name, current_namespace):
    """Evalúa la ruta activa por URL directa, nombre de vista o namespace de la App."""
    # Coincidencia por URL exacta
    if item.get('url') and item['url'] != '#' and item['url'] == current_path:
        return True

    # Coincidencia por patrones o namespaces (ej. 'cotizador:' activa todas las vistas de cotizador)
    active_patterns = item.get('active_patterns', [])
    for pattern in active_patterns:
        if pattern.endswith(':'):  # Es un namespace completo
            if current_namespace == pattern.rstrip(':'):
                return True
        elif pattern in current_url_name:  # Es una vista específica o prefijo
            return True

    return False


def navbar_menu(request):
    # 1. Detectar el módulo dinámicamente por la ruta actual
    if request.path.startswith('/compras/'):
        raw_menu = build_compras_menu()
    else:
        raw_menu = build_default_menu()

    # 2. Permitir sobreescribir desde la vista si se requiere en algún caso especial
    if hasattr(request, 'custom_navbar_items'):
        raw_menu = request.custom_navbar_items

    # 3. Procesar los ítems (permisos, resolución de URLs y cálculo de estado activo)
    processed_menu = process_menu_items(raw_menu, request)

    return {
        'navbar_menu_items': processed_menu
    }
