from django.shortcuts import get_object_or_404, render

from apps.destajos.inlines import PrecioFormset
from apps.destajos.models import Contratista


def precios_formset(request, pk):
    contratista = get_object_or_404(Contratista, pk=pk)

    if request.method == "POST":
        formset = PrecioFormset(request.POST, instance=contratista)

        if formset.is_valid():
            formset.save()

            response = render(
                request,
                'partials/apps/destajos/contratistas/precios.html',
                {
                    'Precio': PrecioFormset(instance=contratista),
                    'contratista': contratista,
                    'saved': True,
                }
            )
            return response
        else:
            response = render(
                request,
                'partials/apps/destajos/contratistas/precios.html',
                {
                    'Precio': PrecioFormset(request.POST, instance=contratista),
                    'contratista': contratista
                }
            )
            return response

    else:
        formset = PrecioFormset(instance=contratista)

    return render(
        request,
        'partials/apps/destajos/contratistas/precios.html',
        {
            'Precio': formset,
            'contratista': contratista
        }
    )
