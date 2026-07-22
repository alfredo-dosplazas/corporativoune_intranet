from django.db import models


class Obras(models.Model):
    descripcion = models.TextField(db_column='Descripcion',
                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    direccion = models.TextField(db_column='Direccion',
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    created = models.DateTimeField(db_column='Created',
                                   db_comment='Fecha en la se creo el registr')  # Field name made lowercase.
    imagen = models.TextField(db_column='Imagen',
                              db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    idcliente = models.CharField(db_column='IdCliente', max_length=13, db_collation='SQL_Latin1_General_CP1_CI_AS',
                                 db_comment='ID del cliente al que pertenec')  # Field name made lowercase.
    idfraccionamiento = models.DecimalField(db_column='IdFraccionamiento', max_digits=5,
                                            decimal_places=0)  # Field name made lowercase.
    nombrecorto = models.CharField(db_column='NombreCorto', max_length=100,
                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idobra = models.CharField(db_column='IdObra', primary_key=True, max_length=20,
                              db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    codigopostal = models.CharField(db_column='CodigoPostal', max_length=10,
                                    db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    calle = models.CharField(db_column='Calle', max_length=60,
                             db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    numeroexterior = models.CharField(db_column='NumeroExterior', max_length=30,
                                      db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    numerointerior = models.CharField(db_column='NumeroInterior', max_length=30,
                                      db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    colonia = models.CharField(db_column='Colonia', max_length=60,
                               db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    localidad = models.CharField(db_column='Localidad', max_length=60,
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    identidadfederativa = models.DecimalField(db_column='IdEntidadFederativa', max_digits=5,
                                              decimal_places=0)  # Field name made lowercase.
    municipio = models.CharField(db_column='Municipio', max_length=60,
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    pais = models.CharField(db_column='Pais', max_length=30,
                            db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    domicilio = models.TextField(db_column='Domicilio',
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.

    def __str__(self):
        return f'{self.nombrecorto} | {self.descripcion}'

    class Meta:
        managed = False
        db_table = 'Obras'


class Presupuestoxpartidas(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    idobra = models.ForeignKey(Obras, on_delete=models.DO_NOTHING, db_column='IdObra', max_length=20,
                               db_comment='Id de la obra a la que pertene',
                               related_name='presupuesto_por_partidas')  # Field name made lowercase.
    claveconceptoobra = models.CharField(db_column='ClaveConceptoObra', max_length=20,
                                         db_collation='SQL_Latin1_General_CP1_CI_AS',
                                         db_comment='Clave de usuario para el conce')  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Descripci¾n del concepto')  # Field name made lowercase. This field type is a guess.
    nivelidentacion = models.DecimalField(db_column='NivelIdentacion', max_digits=2, decimal_places=0,
                                          db_comment='Nivel de identaci¾n del nodo, ')  # Field name made lowercase.
    idconceptoobra = models.DecimalField(db_column='IdConceptoObra', max_digits=10, decimal_places=0,
                                         db_comment='Id interno del concepto de obr')  # Field name made lowercase.
    idconceptopadre = models.DecimalField(db_column='IdConceptoPadre', max_digits=10, decimal_places=0,
                                          db_comment='Id del concepto padre al que s')  # Field name made lowercase.
    signo = models.CharField(db_column='Signo', max_length=1, db_collation='SQL_Latin1_General_CP1_CI_AS',
                             db_comment='Signo que identifica + Cuando ')  # Field name made lowercase.
    visible = models.IntegerField(db_column='Visible',
                                  db_comment='Campo auxiliar para el datatab')  # Field name made lowercase.
    unidad = models.CharField(db_column='Unidad', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS',
                              db_comment='Unidad del concepto')  # Field name made lowercase.
    cantidad = models.FloatField(db_column='Cantidad',
                                 db_comment='Volumen del concepto, acumulad')  # Field name made lowercase.
    preciopresupuestado = models.FloatField(db_column='PrecioPresupuestado',
                                            db_comment='Precio del concepto')  # Field name made lowercase.
    esagrupador = models.IntegerField(db_column='EsAgrupador',
                                      db_comment='Indica si el concepto es un ag')  # Field name made lowercase.
    costodirecto = models.FloatField(db_column='CostoDirecto',
                                     db_comment='Costo directo total del concep')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idordencambio = models.DecimalField(db_column='IdOrdenCambio', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PresupuestoxPartidas'


class Insumosxdeobra(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    idobra = models.ForeignKey(
        Obras,
        on_delete=models.DO_NOTHING,
        db_column='IdObra',
        db_comment='Id de la obra a la que pertene',
        related_name='insumos_de_obra'
    )  # Field name made lowercase.
    idinsumo = models.ForeignKey(
        'Insumosgeneral',
        on_delete=models.DO_NOTHING,
        db_column='IdInsumo',
        related_name='insumos_obras'
    )
    idunidad = models.DecimalField(db_column='IdUnidad', max_digits=5, decimal_places=0)  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Descripci¾n del insumo')  # Field name made lowercase. This field type is a guess.
    comentarios = models.TextField(db_column='Comentarios', db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Comentarios para el insumo')  # Field name made lowercase. This field type is a guess.
    cantidad = models.FloatField(db_column='Cantidad',
                                 db_comment='Cantidad total del insumo que ')  # Field name made lowercase.
    preciopresupuestadoreal = models.FloatField(db_column='PrecioPresupuestadoReal')  # Field name made lowercase.
    preciopresupuestadomn = models.FloatField(db_column='PrecioPresupuestadoMN')  # Field name made lowercase.
    preciopresupuestadome = models.FloatField(db_column='PrecioPresupuestadoME')  # Field name made lowercase.
    idgrupoinsumos = models.DecimalField(db_column='IdGrupoInsumos', max_digits=5,
                                         decimal_places=0)  # Field name made lowercase.
    fsr = models.FloatField(db_column='FSR')  # Field name made lowercase.
    preciopresupuestado = models.FloatField(db_column='PrecioPresupuestado')  # Field name made lowercase.
    idordencambio = models.DecimalField(db_column='IdOrdenCambio', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    fechaimportacion = models.DateTimeField(db_column='FechaImportacion',
                                            db_comment='Fecha en que se import¾ el pre')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    preciopresupuestadorealme = models.FloatField(db_column='PrecioPresupuestadoRealME')  # Field name made lowercase.
    preciopresupuestadorealmn = models.FloatField(db_column='PrecioPresupuestadoRealMN')  # Field name made lowercase.
    cantidadcomprada = models.FloatField(db_column='CantidadComprada',
                                         db_comment='Cantidad total del insumo que ')  # Field name made lowercase.
    importepresupuestado = models.FloatField(db_column='ImportePresupuestado')  # Field name made lowercase.
    importepresupuestadomn = models.FloatField(db_column='ImportePresupuestadoMN')  # Field name made lowercase.
    importepresupuestadome = models.FloatField(db_column='ImportePresupuestadoME')  # Field name made lowercase.
    cantidadporcomprar = models.FloatField(db_column='CantidadPorComprar',
                                           db_comment='Cantidad pendiente de comprar ')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'InsumosXDeObra'


class Insumosgeneral(models.Model):
    idinsumo = models.CharField(db_column='IdInsumo', primary_key=True, max_length=20,
                                db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    idunidad = models.ForeignKey(
        'Unidades',  # Reemplaza por el nombre real de tu modelo de Unidades
        on_delete=models.DO_NOTHING,
        db_column='IdUnidad'
    )

    descripcion = models.TextField(db_column='Descripcion',
                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    ultimopreciocompra = models.FloatField(db_column='UltimoPrecioCompra')  # Field name made lowercase.
    idcccostodirecto = models.CharField(db_column='IdCCCostoDirecto', max_length=20,
                                        db_collation='SQL_Latin1_General_CP1_CI_AS',
                                        db_comment='Id de la cuenta contable aplic')  # Field name made lowercase.
    idgrupoinsumos = models.DecimalField(db_column='IdGrupoInsumos', max_digits=5, decimal_places=0,
                                         db_comment='Id del grupo de insumos al que')  # Field name made lowercase.
    idccingreso = models.CharField(db_column='IdCCIngreso', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Id de la cuenta contable aplic')  # Field name made lowercase.
    aplicadesglosecostoxobra = models.IntegerField(db_column='AplicaDesgloseCostoxObra')  # Field name made lowercase.
    esinventariado = models.IntegerField(db_column='EsInventariado')  # Field name made lowercase.
    aplicadesglosecostoxareacosteo = models.IntegerField(
        db_column='AplicaDesgloseCostoxAreaCosteo')  # Field name made lowercase.
    aplicadesgloseingresoxobra = models.IntegerField(
        db_column='AplicaDesgloseIngresoxObra')  # Field name made lowercase.
    localizacionenalmacen = models.CharField(db_column='LocalizacionEnAlmacen', max_length=30,
                                             db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    numerodeparte = models.CharField(db_column='NumeroDeParte', max_length=20,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idfamiliainsumos = models.ForeignKey(
        'Familiainsumos',
        on_delete=models.DO_NOTHING,
        db_column='IdFamiliaInsumos',
        null=True,
        blank=True
    )
    esinsumoagrupador = models.IntegerField(db_column='EsInsumoAgrupador',
                                            db_comment='Indica que el insumo no es det')  # Field name made lowercase.
    numerodereemplazo = models.CharField(db_column='NumeroDeReemplazo', max_length=20,
                                         db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idtipoinsumo = models.DecimalField(db_column='IdTipoInsumo', max_digits=5, decimal_places=0,
                                       db_comment='ID del tipo de insumo asociado')  # Field name made lowercase.
    inventariominimo = models.FloatField(db_column='InventarioMinimo')  # Field name made lowercase.
    caracteristicas = models.TextField(db_column='Caracteristicas',
                                       db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    recomendacionesdeuso = models.TextField(db_column='RecomendacionesDeUso',
                                            db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    existenciaactual = models.FloatField(db_column='ExistenciaActual')  # Field name made lowercase.
    idimagen = models.TextField(db_column='IdImagen',
                                db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    idsucursal = models.DecimalField(db_column='IdSucursal', max_digits=5,
                                     decimal_places=0)  # Field name made lowercase.
    inventariomaximo = models.FloatField(db_column='InventarioMaximo')  # Field name made lowercase.
    aplicacontrolxseries = models.IntegerField(db_column='AplicaControlxSeries')  # Field name made lowercase.
    aplicadesglosecostoxdepartamento = models.IntegerField(
        db_column='AplicaDesgloseCostoxDepartamento')  # Field name made lowercase.
    aplicadesglosecostoxsucursal = models.IntegerField(
        db_column='AplicaDesgloseCostoxSucursal')  # Field name made lowercase.
    aplicadesglosecostoxequipo = models.IntegerField(
        db_column='AplicaDesgloseCostoxEquipo')  # Field name made lowercase.
    volumenpuntoreorden = models.FloatField(db_column='VolumenPuntoReorden')  # Field name made lowercase.
    esactivo = models.IntegerField(db_column='EsActivo')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idccalmacen = models.CharField(db_column='IdCCAlmacen', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Id de la cuenta contable aplic')  # Field name made lowercase.
    idconceptogastoviviendas = models.DecimalField(db_column='IdConceptoGastoViviendas', max_digits=10,
                                                   decimal_places=0,
                                                   db_comment='Id del concepto de gastos de v')  # Field name made lowercase.
    idconceptodeflujoegreso = models.DecimalField(db_column='IdConceptoDeFlujoEgreso', max_digits=10, decimal_places=0,
                                                  db_comment='Id del concepto de flujo de ti')  # Field name made lowercase.
    idconceptodeflujoingreso = models.DecimalField(db_column='IdConceptoDeFlujoIngreso', max_digits=10,
                                                   decimal_places=0,
                                                   db_comment='Id del concepto de flujo de ti')  # Field name made lowercase.
    aplicadesgloseingresoxareacosteo = models.IntegerField(
        db_column='AplicaDesgloseIngresoxAreaCosteo')  # Field name made lowercase.
    aplicadesgloseingresoxdepartamento = models.IntegerField(
        db_column='AplicaDesgloseIngresoxDepartamento')  # Field name made lowercase.
    aplicadesgloseingresoxequipo = models.IntegerField(
        db_column='AplicaDesgloseIngresoxEquipo')  # Field name made lowercase.
    aplicadesgloseingresoxsucursal = models.IntegerField(
        db_column='AplicaDesgloseIngresoxSucursal')  # Field name made lowercase.
    aplicadesglosealmacenxobra = models.IntegerField(
        db_column='AplicaDesgloseAlmacenXObra')  # Field name made lowercase.
    aplicadesglosealmacenxareacosteo = models.IntegerField(
        db_column='AplicaDesgloseAlmacenxAreaCosteo')  # Field name made lowercase.
    aplicadesglosealmacenxdepartamento = models.IntegerField(
        db_column='AplicaDesgloseAlmacenxDepartamento')  # Field name made lowercase.
    aplicadesglosealmacenxsucursal = models.IntegerField(
        db_column='AplicaDesgloseAlmacenxSucursal')  # Field name made lowercase.
    aplicadesglosealmacenxequipo = models.IntegerField(
        db_column='AplicaDesgloseAlmacenxEquipo')  # Field name made lowercase.
    aplicadesglosealmacenxalmacen = models.IntegerField(
        db_column='AplicaDesgloseAlmacenxAlmacen')  # Field name made lowercase.
    esproducto = models.IntegerField(db_column='EsProducto',
                                     db_comment='Indica que el insumo es un pro')  # Field name made lowercase.
    esbombeado = models.IntegerField(db_column='EsBombeado',
                                     db_comment='Indica que el concreto es bomb')  # Field name made lowercase.
    idtipoproducto = models.DecimalField(db_column='IdTipoProducto', max_digits=5, decimal_places=0,
                                         db_comment='Id del tipo de producto asigna')  # Field name made lowercase.
    idareacompra = models.DecimalField(db_column='IdAreaCompra', max_digits=5,
                                       decimal_places=0)  # Field name made lowercase.
    costodealmacen = models.FloatField(db_column='CostoDeAlmacen')  # Field name made lowercase.
    costodecotizacion = models.FloatField(db_column='CostoDeCotizacion')  # Field name made lowercase.
    porcentajedemargen = models.FloatField(db_column='PorcentajeDeMargen')  # Field name made lowercase.
    preciodelista = models.FloatField(db_column='PrecioDeLista')  # Field name made lowercase.
    idtipodecliente1 = models.DecimalField(db_column='IdTipoDeCliente1', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idtipodecliente2 = models.DecimalField(db_column='IdTipoDeCliente2', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idtipodecliente3 = models.DecimalField(db_column='IdTipoDeCliente3', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idtipodecliente4 = models.DecimalField(db_column='IdTipoDeCliente4', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idtipodecliente5 = models.DecimalField(db_column='IdTipoDeCliente5', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idtipodecliente6 = models.DecimalField(db_column='IdTipoDeCliente6', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    descuentoatipodecliente1 = models.FloatField(db_column='DescuentoATipoDeCliente1')  # Field name made lowercase.
    descuentoatipodecliente2 = models.FloatField(db_column='DescuentoATipoDeCliente2')  # Field name made lowercase.
    descuentoatipodecliente3 = models.FloatField(db_column='DescuentoATipoDeCliente3')  # Field name made lowercase.
    descuentoatipodecliente4 = models.FloatField(db_column='DescuentoATipoDeCliente4')  # Field name made lowercase.
    descuentoatipodecliente5 = models.FloatField(db_column='DescuentoATipoDeCliente5')  # Field name made lowercase.
    descuentoatipodecliente6 = models.FloatField(db_column='DescuentoATipoDeCliente6')  # Field name made lowercase.
    precioatipodecliente1 = models.FloatField(db_column='PrecioATipoDeCliente1')  # Field name made lowercase.
    precioatipodecliente2 = models.FloatField(db_column='PrecioATipoDeCliente2')  # Field name made lowercase.
    precioatipodecliente3 = models.FloatField(db_column='PrecioATipoDeCliente3')  # Field name made lowercase.
    precioatipodecliente4 = models.FloatField(db_column='PrecioATipoDeCliente4')  # Field name made lowercase.
    precioatipodecliente5 = models.FloatField(db_column='PrecioATipoDeCliente5')  # Field name made lowercase.
    precioatipodecliente6 = models.FloatField(db_column='PrecioATipoDeCliente6')  # Field name made lowercase.
    aplicaserie = models.IntegerField(db_column='AplicaSerie')  # Field name made lowercase.
    usapolizadegarantia = models.IntegerField(db_column='UsaPolizaDeGarantia')  # Field name made lowercase.
    idmarca = models.DecimalField(db_column='IdMarca', max_digits=5, decimal_places=0)  # Field name made lowercase.
    esinsumodeventa = models.IntegerField(db_column='EsInsumoDeVenta')  # Field name made lowercase.
    modelo = models.CharField(db_column='Modelo', max_length=25,
                              db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idtipodeingreso = models.IntegerField(db_column='IdTipoDeIngreso')  # Field name made lowercase.
    folio = models.DecimalField(db_column='Folio', max_digits=5, decimal_places=0,
                                db_comment='Folio')  # Field name made lowercase.
    idmoneda = models.DecimalField(db_column='IdMoneda', max_digits=5, decimal_places=0,
                                   db_comment='IdMoneda')  # Field name made lowercase.
    preciodelistamanual = models.IntegerField(db_column='PrecioDeListaManual')  # Field name made lowercase.
    esaditivo = models.IntegerField(db_column='EsAditivo')  # Field name made lowercase.
    idinsumoenlacepresupuesto = models.CharField(db_column='IdInsumoEnlacePresupuesto', max_length=20,
                                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    esempaquedeespecies = models.IntegerField(db_column='EsEmpaqueDeEspecies')  # Field name made lowercase.
    kgsempaque = models.FloatField(db_column='KgsEmpaque')  # Field name made lowercase.
    esautoconsumible = models.IntegerField(db_column='EsAutoconsumible')  # Field name made lowercase.
    idclasificacionmaterial = models.IntegerField(db_column='IdClasificacionMaterial')  # Field name made lowercase.
    idcccostoindirecto = models.CharField(db_column='IdCCCostoIndirecto', max_length=20,
                                          db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idproductoserviciosat = models.CharField(db_column='IdProductoServicioSAT', max_length=8,
                                             db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    seredondeaencomprasalaunidad = models.IntegerField(
        db_column='SeRedondeaEnComprasALaUnidad')  # Field name made lowercase.
    precio = models.FloatField(db_column='Precio')  # Field name made lowercase.
    fechamodificacion = models.DateTimeField(db_column='FechaModificacion')  # Field name made lowercase.
    fechaactualizacion = models.DateTimeField(db_column='FechaActualizacion')  # Field name made lowercase.
    idgrupoinsumosindirectos = models.IntegerField(db_column='IdGrupoInsumosIndirectos')  # Field name made lowercase.
    claveproductoserviciosatcp = models.CharField(db_column='ClaveProductoServicioSATCP', max_length=8,
                                                  db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    esmaterialpeligroso = models.IntegerField(db_column='EsMaterialPeligroso')  # Field name made lowercase.
    clavematerialpeligrososatcp = models.CharField(db_column='ClaveMaterialPeligrosoSATCP', max_length=5,
                                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    pesokg = models.FloatField(db_column='PesoKg')  # Field name made lowercase.
    idverticalvrmx = models.IntegerField(db_column='IdVerticalVRMX')  # Field name made lowercase.
    fechaverticalvrmx = models.DateTimeField(db_column='FechaVerticalVRMX')  # Field name made lowercase.
    esinsumogenerico = models.IntegerField(db_column='EsInsumoGenerico')  # Field name made lowercase.
    tipogasto = models.IntegerField(db_column='TipoGasto')  # Field name made lowercase.
    idp = models.FloatField(db_column='IDP')  # Field name made lowercase.
    cartaportesectorcofepris = models.IntegerField(db_column='CartaPorteSectorCofepris')  # Field name made lowercase.
    cartaportedenominaciongenericaprod = models.CharField(db_column='CartaPorteDenominacionGenericaProd', max_length=50,
                                                          db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaportedenominaciondistintivaprod = models.CharField(db_column='CartaPorteDenominacionDistintivaProd',
                                                            max_length=50,
                                                            db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaportefabricante = models.TextField(db_column='CartaPorteFabricante',
                                            db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaportefechacaducidad = models.DateTimeField(db_column='CartaPorteFechaCaducidad')  # Field name made lowercase.
    cartaportelotemedicamento = models.CharField(db_column='CartaPorteLoteMedicamento', max_length=10,
                                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaporteformafarmaceutica = models.IntegerField(
        db_column='CartaPorteFormaFarmaceutica')  # Field name made lowercase.
    cartaportecondicionesesptransp = models.IntegerField(
        db_column='CartaPorteCondicionesEspTransp')  # Field name made lowercase.
    cartaporteregistrosanitariofolioautorizacion = models.CharField(
        db_column='CartaPorteRegistroSanitarioFolioAutorizacion', max_length=15,
        db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaportenombreingredienteactivo = models.TextField(db_column='CartaPorteNombreIngredienteActivo',
                                                         db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaportenomquimico = models.TextField(db_column='CartaPorteNomQuimico',
                                            db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaportenumcas = models.CharField(db_column='CartaPorteNumCAS', max_length=15,
                                        db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaportenumregsanplagcofepris = models.CharField(db_column='CartaPorteNumRegSanPlagCOFEPRIS', max_length=60,
                                                       db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cartaportedatosfabricante = models.TextField(db_column='CartaPorteDatosFabricante',
                                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaportedatosformulador = models.TextField(db_column='CartaPorteDatosFormulador',
                                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaportedatosmaquilador = models.TextField(db_column='CartaPorteDatosMaquilador',
                                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    cartaporteusoautorizado = models.TextField(db_column='CartaPorteUsoAutorizado',
                                               db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    clasificacion = models.CharField(db_column='Clasificacion', max_length=150,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'InsumosGeneral'


class Cargosordenesdecompra(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    idordencompra = models.CharField(db_column='IdOrdenCompra', max_length=12,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idinsumo = models.ForeignKey(
        Insumosgeneral,
        on_delete=models.DO_NOTHING,
        db_column='IdInsumo',
        max_length=20,
        related_name='cargos_ordenes_compra'
    )

    idrequisicion = models.CharField(db_column='IdRequisicion', max_length=12,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idconceptoobra = models.DecimalField(db_column='IdConceptoObra', max_digits=10,
                                         decimal_places=0)  # Field name made lowercase.
    claveconceptoobra = models.CharField(db_column='ClaveConceptoObra', max_length=20,
                                         db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    idsubobra = models.DecimalField(db_column='IdSubObra', max_digits=10,
                                    decimal_places=0)  # Field name made lowercase.
    idobra = models.ForeignKey(
        Obras,
        on_delete=models.DO_NOTHING,
        db_column='IdObra',
        max_length=20,
        related_name='cargos_ordenes_compra'
    )
    cantidad = models.FloatField(db_column='Cantidad')  # Field name made lowercase.
    idunidad = models.DecimalField(db_column='IdUnidad', max_digits=10, decimal_places=0)  # Field name made lowercase.
    cantidadfacturada = models.FloatField(db_column='CantidadFacturada')  # Field name made lowercase.
    estatusexcedido = models.DecimalField(db_column='EstatusExcedido', max_digits=5,
                                          decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    cantidadcancelada = models.FloatField(db_column='CantidadCancelada')  # Field name made lowercase.
    idareacosteo = models.DecimalField(db_column='IdAreaCosteo', max_digits=5,
                                       decimal_places=0)  # Field name made lowercase.
    idalmacen = models.DecimalField(db_column='IdAlmacen', max_digits=10,
                                    decimal_places=0)  # Field name made lowercase.
    fechaentrega = models.DateTimeField(db_column='FechaEntrega')  # Field name made lowercase.
    tipocosto = models.CharField(db_column='TipoCosto', max_length=3,
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cantidadsurtida = models.FloatField(db_column='CantidadSurtida')  # Field name made lowercase.
    precio = models.FloatField(db_column='Precio')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    idequipo = models.CharField(db_column='IdEquipo', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS',
                                db_comment='Id del equipo al que afecta es')  # Field name made lowercase.
    idordentrabajo = models.CharField(db_column='IdOrdenTrabajo', max_length=13,
                                      db_collation='SQL_Latin1_General_CP1_CI_AS',
                                      db_comment='Id de la OT a la que afecta es')  # Field name made lowercase.
    periododecargo = models.DateTimeField(db_column='PeriodoDeCargo')  # Field name made lowercase.
    idunidadrequisicion = models.DecimalField(db_column='IdUnidadRequisicion', max_digits=3,
                                              decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CargosOrdenesDeCompra'


class Ordenesdecomprad(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    cantidad = models.FloatField(db_column='Cantidad')  # Field name made lowercase.
    precio = models.FloatField(db_column='Precio')  # Field name made lowercase.
    porcentajedescuento = models.FloatField(db_column='PorcentajeDescuento')  # Field name made lowercase.
    idinsumo = models.ForeignKey(
        Insumosgeneral,
        on_delete=models.DO_NOTHING,
        db_column='IdInsumo',
        related_name='detalles_ordenes'
    )
    notas = models.TextField(db_column='Notas',
                             db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    idobra = models.ForeignKey(
        Obras,
        on_delete=models.DO_NOTHING,
        db_column='IdObra',
        related_name='detalles_ordenes_compra'
    )
    idsucursal = models.DecimalField(db_column='IdSucursal', max_digits=2,
                                     decimal_places=0)  # Field name made lowercase.
    idunidad = models.DecimalField(db_column='IdUnidad', max_digits=10, decimal_places=0)  # Field name made lowercase.
    idordencompra = models.CharField(db_column='IdOrdenCompra', max_length=12,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    tipocosto = models.CharField(db_column='TipoCosto', max_length=3,
                                 db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    estatusvolumenexcedido = models.FloatField(db_column='EstatusVolumenExcedido')  # Field name made lowercase.
    estatusprecioexcedido = models.FloatField(db_column='EstatusPrecioExcedido')  # Field name made lowercase.
    idareacosteo = models.DecimalField(db_column='IdAreaCosteo', max_digits=5,
                                       decimal_places=0)  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Descripci¾n personalizada por ')  # Field name made lowercase. This field type is a guess.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    iddepartamento = models.DecimalField(db_column='IdDepartamento', max_digits=10,
                                         decimal_places=0)  # Field name made lowercase.
    idequipo = models.CharField(db_column='IdEquipo', max_length=20,
                                db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    tienecancelaciones = models.IntegerField(db_column='TieneCancelaciones')  # Field name made lowercase.
    cantidadcancelada = models.FloatField(db_column='CantidadCancelada')  # Field name made lowercase.
    motivocancelacion = models.TextField(db_column='MotivoCancelacion',
                                         db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    fechacancelacion = models.DateTimeField(db_column='FechaCancelacion')  # Field name made lowercase.
    idusuariocancelo = models.DecimalField(db_column='IdUsuarioCancelo', max_digits=5,
                                           decimal_places=0)  # Field name made lowercase.
    idusuarioautorizocancelacion = models.DecimalField(db_column='IdUsuarioAutorizoCancelacion', max_digits=10,
                                                       decimal_places=0)  # Field name made lowercase.
    porcentajeiva = models.FloatField(db_column='PorcentajeIVA')  # Field name made lowercase.
    porcentajeretencion1 = models.FloatField(db_column='PorcentajeRetencion1')  # Field name made lowercase.
    porcentajeretencion2 = models.FloatField(db_column='PorcentajeRetencion2')  # Field name made lowercase.
    importeiva = models.FloatField(db_column='ImporteIVA')  # Field name made lowercase.
    importeretencion1 = models.FloatField(db_column='ImporteRetencion1')  # Field name made lowercase.
    importeretencion2 = models.FloatField(db_column='ImporteRetencion2')  # Field name made lowercase.
    importeieps = models.FloatField(db_column='ImporteIEPS')  # Field name made lowercase.
    preciosinieps = models.FloatField(db_column='PrecioSinIEPS')  # Field name made lowercase.
    idalmacen = models.DecimalField(db_column='IdAlmacen', max_digits=10,
                                    decimal_places=0)  # Field name made lowercase.
    fechaentrega = models.DateTimeField(db_column='FechaEntrega')  # Field name made lowercase.
    cantidadentregada = models.FloatField(db_column='CantidadEntregada')  # Field name made lowercase.
    importe = models.FloatField(db_column='Importe')  # Field name made lowercase.
    porcentajeretencion3 = models.FloatField(db_column='PorcentajeRetencion3')  # Field name made lowercase.
    importeretencion3 = models.FloatField(db_column='ImporteRetencion3')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    idordentrabajo = models.CharField(db_column='IdOrdenTrabajo', max_length=13,
                                      db_collation='SQL_Latin1_General_CP1_CI_AS',
                                      db_comment='ID de la OT a la que afecta es')  # Field name made lowercase.
    idcontratoquededuce = models.CharField(db_column='IdContratoQueDeduce', max_length=15,
                                           db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    cantidadfacturada = models.FloatField(db_column='CantidadFacturada')  # Field name made lowercase.
    fechaentregadelproveedor = models.DateTimeField(db_column='FechaEntregaDelProveedor', blank=True,
                                                    null=True)  # Field name made lowercase.
    requisitosdecalidad = models.TextField(db_column='RequisitosDeCalidad',
                                           db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    periododecargo = models.DateTimeField(db_column='PeriodoDeCargo')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'OrdenesDeCompraD'


class Familiainsumos(models.Model):
    idfamilia = models.DecimalField(db_column='IdFamilia', primary_key=True, max_digits=10, decimal_places=0,
                                    db_comment='ID principal de la tabla')  # Field name made lowercase.
    idfamiliaparent = models.DecimalField(db_column='IdFamiliaParent', max_digits=10, decimal_places=0,
                                          db_comment='ID de la familia de la cual es')  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre', max_length=40, db_collation='SQL_Latin1_General_CP1_CI_AS',
                              db_comment='Nombre de la familia')  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion',
                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase. This field type is a guess.
    nivel = models.DecimalField(db_column='Nivel', max_digits=2, decimal_places=0,
                                db_comment='Nivel de identaci¾n del nodo, ')  # Field name made lowercase.
    eshoja = models.IntegerField(db_column='EsHoja',
                                 db_comment='Indica que la familia es un no')  # Field name made lowercase.
    signo = models.CharField(db_column='Signo', max_length=1, db_collation='SQL_Latin1_General_CP1_CI_AS',
                             db_comment='Signo que identifica + Cuando ')  # Field name made lowercase.
    visible = models.IntegerField(db_column='Visible',
                                  db_comment='indica si el nodo es visible e')  # Field name made lowercase.
    orden = models.TextField(db_column='Orden', db_collation='SQL_Latin1_General_CP1_CI_AS',
                             db_comment='Indica el orden asignado en el')  # Field name made lowercase. This field type is a guess.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    fechaactualizacion = models.DateTimeField(db_column='FechaActualizacion')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'FamiliaInsumos'


class Unidades(models.Model):
    nombre = models.CharField(db_column='Nombre', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS',
                              db_comment='Nombre de la unidad')  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', db_collation='SQL_Latin1_General_CP1_CI_AS',
                                   db_comment='Descripci¾n detallada de la un')  # Field name made lowercase. This field type is a guess.
    medidor = models.CharField(db_column='Medidor', max_length=80, db_collation='SQL_Latin1_General_CP1_CI_AS',
                               db_comment='Nombre del dispositivo utiliza')  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5, decimal_places=0,
                                        db_comment='Fecha en que se cre¾ el regist')  # Field name made lowercase.
    idunidad = models.DecimalField(db_column='IdUnidad', primary_key=True, max_digits=5,
                                   decimal_places=0)  # Field name made lowercase.
    idunidadsat = models.CharField(db_column='IdUnidadSAT', max_length=3,
                                   db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    fechaactualizacion = models.DateTimeField(db_column='FechaActualizacion')  # Field name made lowercase.
    idestatus = models.DecimalField(db_column='IdEstatus', max_digits=5, decimal_places=0)  # Field name made lowercase.
    claveunidadcp = models.CharField(db_column='ClaveUnidadCP', max_length=3,
                                     db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Unidades'


class Expinsxpartidas(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    idobra = models.ForeignKey(
        Obras,
        on_delete=models.DO_NOTHING,
        db_column='IdObra',
        related_name='explosiones_insumos'
    )
    idconceptoobra = models.DecimalField(db_column='IdConceptoObra', max_digits=10, decimal_places=0,
                                         db_comment='Id interno del concepto de obr')  # Field name made lowercase.
    idinsumo = models.ForeignKey(
        Insumosgeneral,
        on_delete=models.DO_NOTHING,
        db_column='IdInsumo',
        max_length=20,
        related_name='explosiones_partidas'
    )
    cantidad = models.FloatField(db_column='Cantidad',
                                 db_comment='Cantidad total del insumo que ')  # Field name made lowercase.
    idusuariocreo = models.DecimalField(db_column='IdUsuarioCreo', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.
    created = models.DateTimeField(db_column='Created')  # Field name made lowercase.
    idordencambio = models.DecimalField(db_column='IdOrdenCambio', max_digits=5,
                                        decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ExpInsxPartidas'
