from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from apps.regalos.models import Evento, Regalo, Invitado, CategoriaRegalo
from apps.regalos.tasks import descargar_imagen_regalo_task


class CategoriaPorEventoWidget(ForeignKeyWidget):
    def __init__(self, model, field='nombre', evento=None, *args, **kwargs):
        super().__init__(model, field=field, *args, **kwargs)
        self.evento = evento

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None

        nombre_limpio = str(value).strip()
        if not nombre_limpio:
            return None

        qs = self.get_queryset(value, row, **kwargs)
        if self.evento:
            qs = qs.filter(evento=self.evento)

        # Busca coincidencia insensible a mayúsculas/minúsculas dentro del evento actual
        categoria = qs.filter(nombre__iexact=nombre_limpio).first()
        return categoria  # Devuelve None si no existe (no rompe la importación)


class RegaloResource(resources.ModelResource):
    evento = fields.Field(
        column_name='evento',
        attribute='evento',
        widget=ForeignKeyWidget(Evento, field='slug')
    )
    categoria = fields.Field(
        column_name='categoria',
        attribute='categoria',
        widget=CategoriaPorEventoWidget(CategoriaRegalo, field='nombre')
    )

    class Meta:
        model = Regalo
        fields = ('id', 'evento', 'numero', 'nombre', 'destacado', 'categoria')
        export_order = fields
        import_id_fields = ('evento', 'numero')

    def __init__(self, evento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        self.fields['categoria'].widget.evento = evento

    def before_import_row(self, row, **kwargs):
        if self.evento:
            row['evento'] = self.evento.slug

    def skip_row(self, instance, original, *args, **kwargs):
        """
        Omite la fila si no tiene un número o un nombre válido,
        evitando errores de base de datos por nulos en Regalos.
        """
        if not getattr(instance, 'numero', None) or not getattr(instance, 'nombre', None):
            return True
        return super().skip_row(instance, original, *args, **kwargs)

    def after_save_instance(self, instance, original, *args, **kwargs):
        """
        Se ejecuta después de guardar cada regalo. Si es nuevo y no tiene imagen,
        lanza la tarea de Celery en segundo plano.
        """
        super().after_save_instance(instance, original, *args, **kwargs)

        if not original and not instance.imagen:
            descargar_imagen_regalo_task.delay(instance.pk, instance.nombre)


class InvitadoResource(resources.ModelResource):
    evento = fields.Field(
        column_name='evento',
        attribute='evento',
        widget=ForeignKeyWidget(Evento, field='slug')
    )

    class Meta:
        model = Invitado
        fields = ('id', 'evento', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'grupo',
                  'observaciones')
        export_order = fields
        import_id_fields = ('primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')

    def __init__(self, evento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento

    def before_import_row(self, row, **kwargs):
        if self.evento:
            row['evento'] = self.evento.slug
