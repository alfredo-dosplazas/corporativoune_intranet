from dal import autocomplete
from django.db.models import Q
from django.utils.html import format_html

from apps.papeleria.models.articulos import Articulo


class ArticuloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return Articulo.objects.none()

        qs = Articulo.objects.all()

        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(codigo_vs_dp__icontains=self.q) |
                Q(numero_papeleria__icontains=self.q)
            )

        if usuario.is_superuser:
            return qs

        if usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
            return qs

        qs = qs.filter(mostrar_en_sitio=True)
        return qs

    def get_result_value(self, result):
        return result.pk

    def get_selected_result_label(self, result):
        return result.nombre

    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label(result),
                'selected_text': self.get_selected_result_label(result),
                'url': result.get_absolute_url(),
                'impuesto': result.impuesto,
                'precio': result.precio,
                'importe': result.importe,
            }
            for result in context['object_list']
        ]

    def get_result_label(self, result):
        return format_html(
            """
            <div class="flex items-center gap-3 py-1"
                 data-precio="{precio}"
                 data-impuesto="{impuesto}"
                 data-url="{url}">

                {imagen}

                <div class="flex-1 min-w-0">
                    <p class="font-medium leading-tight truncate">
                        {nombre}
                    </p>

                    <p class="text-xs text-gray-500 truncate">
                        {codigo}{numero}
                    </p>
                </div>

                <div class="text-right text-sm font-semibold whitespace-nowrap">
                    ${precio_fmt}
                </div>
            </div>
            """,
            precio=result.precio or 0,
            impuesto=result.impuesto or 0,
            url=result.get_absolute_url(),
            imagen=format_html(
                '<img src="{}" class="h-8 w-8 rounded object-cover" />',
                result.imagen.url
            ) if result.imagen else "",
            nombre=result.nombre,
            codigo=f"{result.codigo_vs_dp} · " if result.codigo_vs_dp else "",
            numero=result.numero_papeleria or "",
            precio_fmt=f"{result.precio:.2f}",
        )
