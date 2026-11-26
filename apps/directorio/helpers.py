from apps.core.models import Empresa
from apps.core.templatetags.phone_filters import phone_format
from apps.core.utils.network import get_empresas_from_ip, get_client_ip, get_sede_from_ip
from apps.directorio.utils import obtener_sedes_permitidas, obtener_empresas_permitidas
from apps.rrhh.models.sedes import Sede


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


def puede_ver_contacto(user, contacto, request=None):
    if user.is_superuser or user.is_staff:
        return True

    if not user.is_authenticated:
        if not request:
            return False
        sedes_permitidas = obtener_sedes_permitidas(request)
        empresas_permitidas = obtener_empresas_permitidas(request)
        en_sede = (
            contacto.sede_administrativa_id in sedes_permitidas
            or contacto.sedes_visibles.filter(id__in=sedes_permitidas).exists()
        )
        return (contacto.empresa_id in empresas_permitidas) and en_sede

    contacto_user = getattr(user, 'contacto', None)
    if not contacto_user or not user.has_perm("directorio.view_contacto"):
        return False

    sedes_usuario = {contacto_user.sede_administrativa_id} - {None}
    sedes_usuario.update(contacto_user.sedes_consulta.values_list('id', flat=True))
    if request:
        sedes_usuario.update(obtener_sedes_permitidas(request))

    en_sede = (
        contacto.sede_administrativa_id in sedes_usuario
        or contacto.sedes_visibles.filter(id__in=sedes_usuario).exists()
    )
    if not en_sede:
        return False

    if not contacto.mostrar_en_directorio or contacto.esta_archivado:
        return user.has_perm("directorio.change_contacto") or user.has_perm("directorio.delete_contacto")

    return True


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
