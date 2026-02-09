from apps.core.models import Empresa
from apps.core.utils.network import get_client_ip, get_empresa_from_ip


def empresas(request):
    context = {
        'empresas': Empresa.objects.all(),
    }

    return context


def empresa(request):
    if request.user.is_authenticated:
        empresa = request.user.contacto.empresa
    else:
        ip = get_client_ip(request)
        empresa = get_empresa_from_ip(ip)

    if empresa is None:
        empresa = Empresa.objects.get(nombre_corto='Dos Plazas')

    context = {
        'empresa': empresa
    }

    return context
