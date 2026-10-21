from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from apps.regalos.models import Evento, Regalo, Invitado


class RegaloResource(resources.ModelResource):
    evento = fields.Field(
        column_name='evento',
        attribute='evento',
        widget=ForeignKeyWidget(Evento, field='slug')
    )

    class Meta:
        model = Regalo
        fields = ('id', 'evento', 'numero', 'nombre', 'destacado')
        export_order = fields
        import_id_fields = ('numero',)

    def __init__(self, evento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento

    def before_import_row(self, row, **kwargs):
        if self.evento:
            row['evento'] = self.evento.slug

class InvitadoResource(resources.ModelResource):
    evento = fields.Field(
        column_name='evento',
        attribute='evento',
        widget=ForeignKeyWidget(Evento, field='slug')
    )

    class Meta:
        model = Invitado
        fields = ('id', 'evento', 'nombre_completo')
        export_order = fields
        import_id_fields = ('nombre_completo',)

    def __init__(self, evento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento

    def before_import_row(self, row, **kwargs):
        if self.evento:
            row['evento'] = self.evento.slug