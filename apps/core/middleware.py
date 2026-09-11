from django.db.models import Value
from django.db.models.functions import Concat
from inertia import share

from apps.core.context_processors import process_menu_items
from apps.core.models import Empresa
from apps.core.navigation import build_default_menu, build_compras_dock, build_default_dock, build_compras_menu
from apps.evidencias_moldes.navigation import build_evidencias_moldes_dock
from apps.interfaz_sae_coi.navigation import build_interfaz_sae_coi_menu
from apps.resguardos.navigation import build_resguardos_menu


def get_user_permissions(user):
    if not user.is_authenticated:
        return []

    if user.is_superuser:
        from django.contrib.auth.models import Permission
        return list(
            Permission.objects.annotate(
                full_perm=Concat('content_type__app_label', Value('.'), 'codename')
            ).values_list('full_perm', flat=True)
        )

    full_permissions = user.get_all_permissions()

    codenames = [perm.split('.')[1] for perm in full_permissions]

    return list(codenames)


def inertia_share(get_response):
    def middleware(request):
        if request.path.startswith('/interfaz-sae-coi/'):
            raw_menu = build_interfaz_sae_coi_menu()
        elif request.path.startswith('/compras/'):
            raw_menu = build_compras_menu()
        elif request.path.startswith('/resguardos/'):
            raw_menu = build_resguardos_menu()
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

        permissions = get_user_permissions(request.user)

        share(
            request,
            menu=processed_menu,
            mobile_dock=processed_menu_mobile,
            empresas=[e.to_dict() for e in Empresa.objects.all()],
            usuario={
                'username': request.user.username,
                'first_name': getattr(request.user, 'first_name', ''),
                'last_name': getattr(request.user, 'last_name', ''),
                'is_superuser': request.user.is_superuser,
                'contacto': request.user.contacto.to_dict() if request.user.is_authenticated and request.user.contacto else None,
            },
            contacto=request.user.contacto.to_dict() if getattr(request.user, 'contacto', None) else None,
            permissions=permissions,
        )
        return get_response(request)

    return middleware
