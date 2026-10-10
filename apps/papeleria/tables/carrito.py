from django.utils.safestring import mark_safe
from django_tables2 import tables

from apps.papeleria.models.articulos import Articulo


class ArticuloCarritoTable(tables.Table):
    acciones = tables.Column(empty_values=(), verbose_name="Acción", orderable=False)

    class Meta:
        model = Articulo
        fields = ['codigo_vs_dp', 'nombre', 'unidad', 'importe', 'acciones']
        attrs = {'class': 'table table-zebra w-full align-middle text-xs'}

    def render_acciones(self, record):
        return mark_safe(f'''
            <form method="post" action="/papeleria/catalogo-articulos/agregar/" class="flex items-center gap-1">
                <input type="hidden" name="csrfmiddlewaretoken" value="{self.request.META.get('CSRF_COOKIE', '')}">
                <input type="hidden" name="articulo_id" value="{record.id}">
                <input type="number" name="cantidad" value="1" min="1" class="input input-xs input-bordered w-12 text-center p-0 font-mono">
                <button type="submit" class="btn btn-primary btn-xs gap-1">
                    <span class="icon-[tabler--plus] text-xs"></span>
                    <span>Agregar</span>
                </button>
            </form>
        ''')
