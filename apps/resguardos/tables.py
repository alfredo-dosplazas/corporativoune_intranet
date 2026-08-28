import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse
from .models import Resguardo


class ResguardoTable(tables.Table):
    # Columna personalizada para el ID o Folio con enlace al detalle
    id = tables.Column(verbose_name="Folio", linkify=lambda record: reverse('resguardos:detail', args=[record.pk]))

    equipo = tables.Column(accessor='equipo.nombre', verbose_name="Equipo")
    numero_serie = tables.Column(accessor='equipo.numero_serie', verbose_name="N° Serie")
    recibe_nombre = tables.Column(verbose_name="Asignado a")
    recibe_puesto_area = tables.Column(verbose_name="Puesto / Área")
    fecha_entrega = tables.DateColumn(verbose_name="Fecha Entrega", format="d/m/Y")

    # Renderizado personalizado para el estado del resguardo
    estado_resguardo = tables.Column(verbose_name="Estado")

    # Indicador visual si está firmado digitalmente/subido
    firmado_digital = tables.Column(verbose_name="Firmado")

    # Acciones
    acciones = tables.Column(empty_values=(), verbose_name="Acciones", orderable=False)

    class Meta:
        model = Resguardo
        fields = (
            'id',
            'equipo',
            'numero_serie',
            'recibe_nombre',
            'recibe_puesto_area',
            'fecha_entrega',
            'estado_resguardo',
            'firmado_digital',
            'acciones'
        )
        attrs = {
            'class': 'table table-hover table-striped align-middle',
        }

    def render_estado_resguardo(self, value):
        badge_class = {
            'ACTIVO': 'bg-success',
            'DEVUELTO': 'bg-secondary',
            'CANCELADO': 'bg-danger',
        }.get(value, 'bg-info')
        return format_html('<span class="badge {}">{}</span>', badge_class, value)

    def render_firmado_digital(self, value):
        if value:
            return format_html('<span class="badge bg-primary"><i class="fas fa-check"></i> Firmado</span>')
        return format_html('<span class="badge bg-warning text-dark"><i class="fas fa-clock"></i> Pendiente</span>')

    def render_acciones(self, record):
        url_detail = reverse('resguardos:detail', args=[record.pk])
        url_print = reverse('resguardos:print', args=[record.pk])  # Para reimpresión/PDF

        return format_html(
            '<div class="btn-group btn-group-sm">'
            '<a href="{}" class="btn btn-outline-primary" title="Ver Detalle"><i class="fas fa-eye"></i></a>'
            '<a href="{}" target="_blank" class="btn btn-outline-secondary" title="Imprimir / PDF"><i class="fas fa-print"></i></a>'
            '</div>',
            url_detail,
            url_print
        )
