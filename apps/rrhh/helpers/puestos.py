def puede_ver_puesto(user, puesto):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.view_puesto")
            and user.contacto.empresa == puesto.empresa
    )


def puede_editar_puesto(user, puesto):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.change_puesto")
            and user.contacto.empresa == puesto.empresa
    )


def puede_eliminar_puesto(user, puesto):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.delete_puesto")
            and user.contacto.empresa == puesto.empresa
    )
