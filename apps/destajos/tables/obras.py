from django_tables2 import Column

from apps.core.tables import TableWithActions
from apps.destajos.models import Obra


class ObraTable(TableWithActions):
    actions_template = "components/apps/destajos/obras/table/actions.html"

    razon_social = Column(accessor='razon_social__nombre_corto')

    class Meta:
        model = Obra
        fields = [
            'nombre',
            'etapa',
            'razon_social',
            'fecha_inicio',
            'fecha_fin',
        ]
