from apps.directorio.utils import obtener_empresas_permitidas


def puede_ver_puesto(request, puesto):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.view_puesto")
            and puesto.empresa.id in empresas_permitidas
    )


def puede_editar_puesto(request, puesto):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.change_puesto")
            and puesto.empresa.id in empresas_permitidas
    )


def puede_eliminar_puesto(request, puesto):
    user = request.user

    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    empresas_permitidas = obtener_empresas_permitidas(request)

    return (
            user.has_perm("rrhh.delete_puesto")
            and puesto.empresa.id in empresas_permitidas
    )
