from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Paquete, Trabajo, PrecioContratista, Contratista, Estructura


class PaqueteResource(resources.ModelResource):
    clave = fields.Field(
        column_name="clave",
        attribute="clave",
    )

    nombre = fields.Field(
        column_name="nombre",
        attribute="nombre",
    )

    padre = fields.Field(
        column_name="padre",
        attribute="padre",
        widget=ForeignKeyWidget(
            Paquete,
            field="clave"
        )
    )

    orden = fields.Field(
        column_name="orden",
        attribute="orden",
    )

    class Meta:
        model = Paquete
        import_id_fields = ("clave",)
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if 'nombre' in row and row['nombre']:
            row['nombre'] = row['nombre'].strip()

        if 'clave' in row and row['clave']:
            row['clave'] = row['clave'].strip()


class TrabajoResource(resources.ModelResource):
    clave = fields.Field(
        column_name="clave",
        attribute="clave",
    )

    nombre = fields.Field(
        column_name="nombre",
        attribute="nombre",
    )

    paquete = fields.Field(
        column_name="paquete",
        attribute="paquete",
        widget=ForeignKeyWidget(
            Paquete,
            field="clave"
        )
    )

    es_unitario = fields.Field(
        column_name="es_unitario",
        attribute="es_unitario",
    )

    unidad = fields.Field(
        column_name="unidad",
        attribute="unidad",
    )

    class Meta:
        model = Trabajo
        import_id_fields = ("clave",)
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if 'nombre' in row and row['nombre']:
            row['nombre'] = row['nombre'].strip()

        if 'clave' in row and row['clave']:
            row['clave'] = row['clave'].strip()


class PrecioContratistaResource(resources.ModelResource):
    contratista = fields.Field(
        column_name="contratista",
        attribute="contratista",
        widget=ForeignKeyWidget(
            Contratista,
            field="nombre"
        )
    )

    trabajo = fields.Field(
        column_name="trabajo",
        attribute="trabajo",
        widget=ForeignKeyWidget(
            Trabajo,
            field="clave"
        )
    )

    estructura = fields.Field(
        column_name="estructura",
        attribute="estructura",
        widget=ForeignKeyWidget(
            Estructura,
            field="nombre"
        )
    )

    precio = fields.Field(
        column_name="precio",
        attribute="precio",
    )

    unidad = fields.Field(
        column_name="unidad",
        attribute="unidad",
        default="vivienda",
    )

    vigente_desde = fields.Field(
        column_name="vigente_desde",
        attribute="vigente_desde",
    )

    vigente_hasta = fields.Field(
        column_name="vigente_hasta",
        attribute="vigente_hasta",
    )

    class Meta:
        model = PrecioContratista
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True
