from apps.core.templatetags.phone_filters import phone_format
from apps.core.utils.network import get_empresas_from_ip, get_client_ip, get_sede_from_ip


def puede_editar_contacto(user, contacto):
    if not user.is_authenticated:
        return False

    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.change_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )


def puede_ver_contacto(user, contacto, request):
    if not user.is_authenticated:
        ip = get_client_ip(request)
        empresas = get_empresas_from_ip(ip)
        sede = get_sede_from_ip(ip)

        return (
            contacto.sede_administrativa == sede or
            sede in contacto.sedes_visibles.all() and
            contacto.empresa in empresas
        )

    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.view_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )


def puede_eliminar_contacto(user, contacto):
    if not user.is_authenticated:
        return False

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
