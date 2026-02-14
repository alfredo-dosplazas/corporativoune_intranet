from apps.core.templatetags.phone_filters import phone_format
from apps.core.utils.network import get_empresas_from_ip, get_client_ip, get_sede_from_ip


def puede_editar_contacto(user, contacto):
    if user.is_superuser:
        return True

    if not user.is_authenticated:
        return False

    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.change_contacto")
            and (
                    user.contacto.sede_administrativa == contacto.sede_administrativa or user.contacto.sede_administrativa in contacto.sedes_visibles.all())
    )


def puede_ver_contacto(user, contacto, request):
    if user.is_superuser:
        return True

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

    puede_ver = (
            user.has_perm("directorio.view_contacto")
            and (
                    user.contacto.sede_administrativa == contacto.sede_administrativa or user.contacto.sede_administrativa in contacto.sedes_visibles.all()
            )
    )

    if not contacto.mostrar_en_directorio:
        puede_ver = (
                puede_ver and user.has_perm("directorio.change_contacto") or user.has_perm("directorio_delete_contacto")
        )

    return puede_ver


def puede_eliminar_contacto(user, contacto):
    if user.is_superuser:
        return True

    if not user.is_authenticated:
        return False

    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.delete_contacto")
            and (
                    user.contacto.sede_administrativa == contacto.sede_administrativa or user.contacto.sede_administrativa in contacto.sedes_visibles.all())
    )


def format_telefono(tel):
    label = phone_format(tel.telefono)
    if tel.extension:
        label += f" ext. {tel.extension}"
    return label
