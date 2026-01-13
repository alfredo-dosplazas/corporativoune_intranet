from apps.core.models import Empresa


def empresas(request):
    context = {
        'empresas': Empresa.objects.all(),
    }

    return context
