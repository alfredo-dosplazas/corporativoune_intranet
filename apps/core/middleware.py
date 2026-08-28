from django.contrib import messages
from inertia import share

from apps.core.context_processors import process_menu_items
from apps.core.navigation import build_default_menu, build_compras_dock, build_default_dock
from apps.evidencias_moldes.navigation import build_evidencias_moldes_dock
from apps.interfaz_sae_coi.navigation import build_interfaz_sae_coi_menu
from intranet import settings


def inertia_share(get_response):
    def middleware(request):
        django_messages = [
            {"level": message.tags, "message": message.message}
            for message in messages.get_messages(request)
        ]

        if request.path.startswith('/interfaz-sae-coi/'):
            raw_menu = build_interfaz_sae_coi_menu()
        else:
            raw_menu = build_default_menu()

        if hasattr(request, 'custom_navbar_items'):
            raw_menu = request.custom_navbar_items

        processed_menu = process_menu_items(raw_menu, request)

        path = request.path
        if path.startswith('/compras/'):
            raw_menu = build_compras_dock()
        elif path.startswith('/evidencias-moldes/'):
            raw_menu = build_evidencias_moldes_dock()
        else:
            raw_menu = build_default_dock()

        processed_menu_mobile = process_menu_items(raw_menu, request)

        share(
            request,
            menu=processed_menu,
            mobile_dock=processed_menu_mobile,
            flash={
                'success': next((m['message'] for m in django_messages if 'success' in m['level']), None),
                'error': next((m['message'] for m in django_messages if 'error' in m['level']), None),
            }
        )
        return get_response(request)

    return middleware
