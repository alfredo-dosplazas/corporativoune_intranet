from django.db import models

class Obras(models.Model):
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    direccion = models.TextField(db_column='Direccion', db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    created = models.DateTimeField(db_column='Created', db_comment='Fecha en la se creo el registr')  # Field name made lowercase.
    imagen = models.TextField(db_column='Imagen', db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    idcliente = models.CharField(db_column='IdCliente', max_length=13, db_collation='SQL_Latin1_General_CP1_CI_AS', db_comment='ID del cliente al que pertenec')  # Field name made lowercase.
    idfraccionamiento = models.DecimalField(db_column='IdFraccionamiento', max_digits=5, decimal_places=0)  # Field name made lowercase.
    nombrecorto = models.CharField(db_column='NombreCorto', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idobra = models.CharField(db_column='IdObra', primary_key=True, max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    codigopostal = models.CharField(db_column='CodigoPostal', max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    calle = models.CharField(db_column='Calle', max_length=60, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    numeroexterior = models.CharField(db_column='NumeroExterior', max_length=30, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    numerointerior = models.CharField(db_column='NumeroInterior', max_length=30, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    colonia = models.CharField(db_column='Colonia', max_length=60, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    localidad = models.CharField(db_column='Localidad', max_length=60, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    identidadfederativa = models.DecimalField(db_column='IdEntidadFederativa', max_digits=5, decimal_places=0)  # Field name made lowercase.
    municipio = models.CharField(db_column='Municipio', max_length=60, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    pais = models.CharField(db_column='Pais', max_length=30, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    domicilio = models.TextField(db_column='Domicilio', db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.

    def __str__(self):
        return f'{self.nombrecorto} | {self.descripcion}'

    class Meta:
        managed = False
        db_table = 'Obras'

class Presupuestoxpartidas(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    idobra = models.ForeignKey(Obras, on_delete=models.DO_NOTHING, db_column='IdObra', max_length=20, db_comment='Id de la obra a la que pertene', related_name='presupuesto_por_partidas')  # Field name made lowercase.
    claveconceptoobra = models.CharField(db_column='ClaveConceptoObra', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', db_comment='Clave de usuario para el conce')  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS', db_comment='Descripci¾n del concepto')  # Field name made lowercase. This field type is a guess.
    nivelidentacion = models.DecimalField(db_column='NivelIdentacion', max_digits=2, decimal_places=0, db_comment='Nivel de identaci¾n del nodo, ')  # Field name made lowercase.
    idconceptoobra = models.DecimalField(db_column='IdConceptoObra', max_digits=10, decimal_places=0, db_comment='Id interno del concepto de obr')  # Field name made lowercase.
    idconceptopadre = models.DecimalField(db_column='IdConceptoPadre', max_digits=10, decimal_places=0, db_comment='Id del concepto padre al que s')  # Field name made lowercase.
    signo = models.CharField(db_column='Signo', max_length=1, db_collation='SQL_Latin1_General_CP1_CI_AS', db_comment='Signo que identifica + Cuando ')  # Field name made lowercase.
    visible = models.IntegerField(db_column='Visible', db_comment='Campo auxiliar para el datatab')  # Field name made lowercase.
    unidad = models.CharField(db_column='Unidad', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', db_comment='Unidad del concepto')  # Field name made lowercase.
    cantidad = models.FloatField(db_column='Cantidad', db_comment='Volumen del concepto, acumulad')  # Field name made lowercase.
    preciopresupuestado = models.FloatField(db_column='PrecioPresupuestado', db_comment='Precio del concepto')  # Field name made lowercase.
    esagrupador = models.IntegerField(db_column='EsAgrupador', db_comment='Indica si el concepto es un ag')  # Field name made lowercase.
    costodirecto = models.FloatField(db_column='CostoDirecto', db_comment='Costo directo total del concep')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5, decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idordencambio = models.DecimalField(db_column='IdOrdenCambio', max_digits=5, decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PresupuestoxPartidas'

