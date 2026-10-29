from apps.directorio.utils import obtener_empresas_permitidas


def puede_ver_area(request, area):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.view_area")
            and area.empresa.id in empresas_permitidas
    )


def puede_editar_area(request, area):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.change_area")
            and area.empresa.id in empresas_permitidas
    )


def puede_eliminar_area(request, area):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.delete_area")
            and area.empresa.id in empresas_permitidas
    )
