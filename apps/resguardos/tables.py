import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse
from .models import Resguardo, Equipo
from ..core.tables import TableWithActions

import django_tables2 as tables
from apps.resguardos.models import Resguardo
# Ajusta la importación de tu TableWithActions según corresponda en tu proyecto:
from apps.core.tables import TableWithActions


class ResguardoTable(TableWithActions):
    actions_template = 'components/apps/resguardos/table/actions.html'

    id = tables.Column(
        verbose_name="ID",
        linkify=lambda record: record.get_absolute_url(),
        attrs={'th': {'class': 'w-16'}, 'td': {'class': 'font-semibold'}}
    )

    equipo = tables.Column(
        verbose_name="Equipo",
        accessor='equipo',
        orderable=True
    )

    recibe_nombre = tables.Column(
        verbose_name="Recibe",
        accessor='recibe_nombre'
    )

    recibe_puesto_area = tables.Column(
        verbose_name="Puesto / Área",
        accessor='recibe_puesto_area'
    )

    estado_resguardo = tables.Column(
        verbose_name="Estado",
        attrs={
            'td': {
                'class': lambda record: (
                    'text-success font-medium' if record.estado_resguardo == 'ACTIVO' else
                    'text-info font-medium' if record.estado_resguardo == 'DEVUELTO' else
                    'text-error font-medium'
                )
            }
        }
    )

    fecha_entrega = tables.DateColumn(
        verbose_name="Fecha Entrega",
        format="d/m/Y"
    )

    class Meta:
        model = Resguardo
        fields = (
            'id',
            'equipo',
            'recibe_nombre',
            'recibe_puesto_area',
            'estado_resguardo',
            'fecha_entrega'
        )


class EquipoTable(TableWithActions):
    actions_template = 'components/apps/resguardos/equipos/table/actions.html'

    id = tables.Column(
        verbose_name="ID",
        linkify=lambda record: reverse('resguardos:equipos__update', args=[record.pk]),
        attrs={'th': {'class': 'w-16'}, 'td': {'class': 'font-semibold'}}
    )

    empresa = tables.Column(
        verbose_name="Empresa",
        accessor='empresa'
    )

    nombre = tables.Column(
        verbose_name="Equipo / Modelo",
        accessor='nombre',
        attrs={'td': {'class': 'font-medium text-base-content'}}
    )

    numero_serie = tables.Column(
        verbose_name="Número de Serie",
        accessor='numero_serie',
        attrs={'td': {'class': 'font-mono text-xs'}}
    )

    identificador_interno = tables.Column(
        verbose_name="Tag / ID Interno",
        accessor='identificador_interno',
        attrs={'td': {'class': 'font-mono text-xs'}}
    )

    estado_actual = tables.Column(
        verbose_name="Estado Actual",
        attrs={
            'td': {
                'class': lambda record: (
                    'text-success font-medium' if record.estado_actual == 'NUEVO' else
                    'text-info font-medium' if record.estado_actual == 'USADO' else
                    'text-warning font-medium' if record.estado_actual == 'DANIADO' else
                    'text-error font-medium'
                )
            }
        }
    )

    ubicacion_fisica_actual = tables.Column(
        verbose_name="Ubicación Física",
        accessor='ubicacion_fisica_actual'
    )

    class Meta:
        model = Equipo
        fields = (
            'id',
            'empresa',
            'nombre',
            'numero_serie',
            'identificador_interno',
            'estado_actual',
            'ubicacion_fisica_actual',
        )
