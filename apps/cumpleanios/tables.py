from django.db.models.functions import ExtractDay, ExtractMonth
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2 import Table, Column

from apps.core.tables import EmpresaBadgeColumn
from apps.cumpleanios.models import Cumpleanero


class CumpleaneroColumn(Column):
    def render(self, value, record):
        url = reverse("directorio:detail", args=[record.pk])
        avatar_url = record.foto.url if record.foto else "/static/img/avatar.png"
        nombre = record.nombre_completo
        edad = getattr(record, "edad_actual", None)

        hoy_badge = ""
        ring_cls = "ring-1 ring-base-300"
        if getattr(record, "es_hoy", False):
            ring_cls = "ring-2 ring-primary"
            hoy_badge = (
                '<span class="badge badge-primary badge-xs font-semibold ml-1.5">¡Hoy!</span>'
            )

        edad_html = (
            f'<span class="text-[11px] text-base-content/60">{edad} años</span>'
            if edad is not None else ""
        )

        return mark_safe(f"""
            <div class="flex items-center gap-2.5 min-w-[180px]">
                <div class="avatar shrink-0">
                    <div class="w-9 h-9 rounded-full {ring_cls} overflow-hidden">
                        <img src="{avatar_url}"
                             alt="{nombre}"
                             class="w-full h-full object-cover"
                             loading="lazy" />
                    </div>
                </div>
                <div class="min-w-0 leading-tight">
                    <div class="flex items-center">
                        <a href="{url}"
                           class="text-xs font-semibold text-primary hover:underline truncate">
                            {nombre}
                        </a>
                        {hoy_badge}
                    </div>
                    <div class="flex items-center gap-1 mt-0.5">
                        {edad_html}
                    </div>
                </div>
            </div>
        """)


class CumpleaneroTable(Table):
    cumpleanero = CumpleaneroColumn(
        empty_values=(),
        order_by=["primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido"],
        verbose_name="Cumpleañero",
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "px-2.5 py-1.5"},
        },
    )
    fecha_nacimiento = Column(
        verbose_name="Fecha",
        attrs={
            "th": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-2"},
            "td": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-1.5 font-mono"},
        },
    )
    empresa = EmpresaBadgeColumn(
        verbose_name="Empresa",
        attrs={
            "th": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-2"},
            "td": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-1.5"},
        },
    )

    class Meta:
        model = Cumpleanero
        fields = [
            "cumpleanero",
            "fecha_nacimiento",
            "empresa",
        ]
        attrs = {
            "class": "table table-xs table-zebra w-full align-middle",
        }

    def order_fecha_nacimiento(self, queryset, is_descending):
        prefix = "-" if is_descending else ""
        queryset = queryset.annotate(
            _mes_cumple=ExtractMonth("fecha_nacimiento"),
            _dia_cumple=ExtractDay("fecha_nacimiento"),
        ).order_by(
            f"{prefix}_mes_cumple",
            f"{prefix}_dia_cumple",
            "primer_apellido",
            "primer_nombre",
        )
        return (queryset, True)