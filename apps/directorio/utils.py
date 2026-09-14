import ipaddress

from apps.core.models import Empresa, EmpresaIPRange
from apps.core.utils.network import get_client_ip
from apps.rrhh.models.sedes import Sede, SedeIPRange


def es_frescopack(user):
    if not hasattr(user, "contacto"):
        return False

    return (
            user.contacto.empresa
            and user.contacto.empresa.nombre_corto == "Frescopack"
    )


def obtener_sedes_permitidas(request):
    """
    Retorna los IDs de las Sedes que el usuario actual (o su IP)
    tiene permitido visualizar en el directorio.
    """
    user = request.user

    # 1. Superusuarios o Staff ven todas las sedes
    if user.is_staff or user.is_superuser:
        return Sede.objects.values_list('id', flat=True)

    sedes_ids = set()

    # 2. Visibilidad por Red / IP de origen
    ip_cliente = get_client_ip(request)
    if ip_cliente:
        try:
            ip_obj = ipaddress.ip_address(ip_cliente)
            # Evaluamos rangos de red vinculados a las sedes
            for rango in SedeIPRange.objects.filter(activa=True).select_related('sede'):
                if ip_obj in ipaddress.ip_network(rango.cidr):
                    sedes_ids.add(rango.sede_id)
        except ValueError:
            pass

    # 3. Visibilidad por usuario autenticado (Sede principal + Sedes adicionales)
    if user.is_authenticated and hasattr(user, 'contacto') and user.contacto:
        contacto = user.contacto

        # Sede física/administrativa propia
        if contacto.sede_administrativa_id:
            sedes_ids.add(contacto.sede_administrativa_id)

        # Sedes adicionales configuradas explícitamente en el ManyToMany
        sedes_visibles = contacto.sedes_visibles.values_list('id', flat=True)
        sedes_ids.update(sedes_visibles)

    return list(sedes_ids)


def obtener_empresas_permitidas(request):
    """
    Retorna los IDs de las empresas a las que el usuario actual
    o su segmento de red tienen acceso de lectura.
    """
    user = request.user

    # 1. Si es Superusuario o Staff, ve todo
    if user.is_staff or user.is_superuser:
        return Empresa.objects.values_list('id', flat=True)

    empresas_ids = set()

    # 2. Filtrado por Red (IP de la petición)
    ip_cliente = get_client_ip(request)
    if ip_cliente:
        try:
            ip_obj = ipaddress.ip_address(ip_cliente)
            # Obtenemos empresas cuyas redes configuradas coincidan con la IP actual
            for rango in EmpresaIPRange.objects.filter(activa=True).select_related('empresa'):
                if ip_obj in ipaddress.ip_network(rango.cidr):
                    empresas_ids.add(rango.empresa_id)
        except ValueError:
            pass

    # 3. Filtrado por asignación de Usuario (Contacto vinculado)
    if user.is_authenticated and hasattr(user, 'contacto') and user.contacto:
        contacto = user.contacto

        # Su empresa principal
        if contacto.empresa_id:
            empresas_ids.add(contacto.empresa_id)

        # Empresas secundarias/relacionadas a las que tiene acceso (ej. Gerente de sistemas)
        relacionadas = contacto.empresas_relacionadas.values_list('id', flat=True)
        empresas_ids.update(relacionadas)

    return list(empresas_ids)
