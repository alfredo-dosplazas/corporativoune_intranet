from django_tables2 import LinkColumn, A

from apps.core.tables import TableWithActions
from apps.votaciones.models import EventoVotacion


class EventoVotacionTable(TableWithActions):
    actions_template = 'components/apps/votaciones/evento/table/actions.html'

    titulo = LinkColumn("votaciones:detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

    class Meta:
        model = EventoVotacion
        fields = [
            'titulo',
            'descripcion',
            'activo',
            'fecha_inicio',
            'fecha_fin',
        ]
