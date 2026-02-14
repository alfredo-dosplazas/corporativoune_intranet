from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2 import Table, Column

from apps.core.tables import EmpresaBadgeColumn
from apps.cumpleanios.models import Cumpleanero


class CumpleaneroColumn(Column):
    def render(self, value, record):
        url = reverse("directorio:detail", args=[record.pk])
        avatar_url = record.foto.url if record.foto else "/static/img/avatar.png"

        badge = ""
        avatar_extra_class = ""

        if record.es_hoy:
            badge = """
                <span class="badge badge-danger ms-2">
                    🎂 ¡Hoy!
                </span>
            """
            avatar_extra_class = "birthday-avatar"

        return mark_safe(f"""
        <div class="position-absolute top-0 start-50 translate-middle">
            🎉
        </div>
            <div class="d-flex align-items-center">
                <div class="position-relative me-3">
                    <img src="{avatar_url}"
                         class="rounded-circle {avatar_extra_class}"
                         width="48" height="48"
                         style="object-fit: cover;">
                </div>
                <div>
                    <a href="{url}" class="fw-semibold text-decoration-none text-primary">
                        {record.nombre_completo}
                    </a>
                    <div class="text-muted small">
                        {record.edad_actual} años
                        {badge}
                    </div>
                </div>
            </div>
        """)


class CumpleaneroTable(Table):
    cumpleanero = CumpleaneroColumn(
        empty_values=(),
        verbose_name='Cumpleañero'
    )
    empresa = EmpresaBadgeColumn(verbose_name='Empresa')

    class Meta:
        model = Cumpleanero
        fields = [
            'cumpleanero',
            'fecha_nacimiento',
            'empresa',
        ]
        attrs = {
            "class": "table align-middle"
        }
