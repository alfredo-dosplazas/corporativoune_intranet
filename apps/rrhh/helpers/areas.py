def puede_ver_area(user, area):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.view_area")
            and user.contacto.empresa == area.empresa
    )


def puede_editar_area(user, area):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.change_area")
            and user.contacto.empresa == area.empresa
    )


def puede_eliminar_area(user, area):
    if user.is_superuser:
        return True

    if not user.contacto:
        return False

    return (
            user.has_perm("rrhh.delete_area")
            and user.contacto.empresa == area.empresa
    )
