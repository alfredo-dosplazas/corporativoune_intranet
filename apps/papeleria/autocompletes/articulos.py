from dal import autocomplete
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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
            <div class="flex gap-4 items-center"
                 data-precio="{}"
                 data-impuesto="{}"
                 data-url="{}">
                {}
                <div class="flex gap-4 items-center">
                    <p class="font-medium">{}</p>
                    <span>|</span>
                    <p>{}</p>
                    <span>|</span>
                    <p>{}</p>
                </div>
            </div>
            """,
            result.precio or 0,
            result.impuesto or 0,
            result.get_absolute_url() if hasattr(result, "get_absolute_url") else "",
            format_html(
                '<img src="{}" class="h-10 w-10 rounded" />',
                result.imagen.url
            ) if result.imagen else "",
            result.nombre,
            result.codigo_vs_dp or "",
            result.numero_papeleria or "",
        )
