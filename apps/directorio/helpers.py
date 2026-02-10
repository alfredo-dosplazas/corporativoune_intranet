from apps.core.templatetags.phone_filters import phone_format


def puede_editar_contacto(user, contacto):
    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.change_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )


def puede_ver_contacto(user, contacto):
    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.view_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )


def puede_eliminar_contacto(user, contacto):
    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.delete_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )


def format_telefono(tel):
    label = phone_format(tel.telefono)
    if tel.extension:
        label += f" ext. {tel.extension}"
    return label
