import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, Q, Max
from django.utils.timezone import now

from apps.core.models import RazonSocial

UNIDADES = (
    ['vivienda', 'VIVIENDA'],
)


class Estructura(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    abreviatura = models.CharField(blank=True, null=True, max_length=50)

    def __str__(self):
        return self.nombre


class Paquete(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subpaquetes"
    )

    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.clave} - {self.nombre}"

    class Meta:
        ordering = (
            'padre__clave',
            'padre_id',
            'orden',
            'clave',
        )


class Trabajo(models.Model):
    clave = models.CharField(max_length=30, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=512)

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        related_name="trabajos"
    )

    es_unitario = models.BooleanField(
        default=True,
        help_text="Si depende del número de viviendas"
    )

    unidad = models.CharField(
        max_length=50,
        blank=True,
        help_text="m2, pza, vivienda, ml, etc",
        choices=UNIDADES,
        default='vivienda'
    )

    def save(self, *args, **kwargs):
        if not self.clave:
            prefijo = self.paquete.clave  # ej. CIM, EST-PB

            # Buscar el último consecutivo del paquete
            ultimo = (
                Trabajo.objects
                .filter(paquete=self.paquete, clave__startswith=f"{prefijo}-")
                .aggregate(max_clave=Max('clave'))
                ['max_clave']
            )

            if ultimo:
                match = re.search(r'-(\d+)$', ultimo)
                siguiente = int(match.group(1)) + 1 if match else 1
            else:
                siguiente = 1

            self.clave = f"{prefijo}-{siguiente:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ('paquete', 'nombre')


class EstructuraTrabajo(models.Model):
    estructura = models.ForeignKey(
        Estructura,
        on_delete=models.CASCADE,
        related_name="trabajos"
    )

    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.CASCADE
    )

    cantidad_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )

    class Meta:
        unique_together = ("estructura", "trabajo")


class Contratista(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    rfc = models.CharField(max_length=13, unique=True, blank=True, null=True, verbose_name='RFC')

    correo_electronico = models.EmailField(blank=True, null=True, verbose_name='Correo electrónico')
    telefono = models.CharField(max_length=11, blank=True, null=True, verbose_name='Teléfono')

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class PrecioContratista(models.Model):
    contratista = models.ForeignKey(Contratista, on_delete=models.CASCADE, related_name='precios')
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)
    estructura = models.ForeignKey(
        Estructura,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    precio = models.DecimalField(max_digits=10, decimal_places=2)
    unidad = models.CharField(max_length=50, choices=UNIDADES, default='vivienda')

    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(blank=True, null=True)

    @classmethod
    def precio_vigente(cls, contratista, trabajo, fecha=None):
        fecha = fecha or now().date()

        return (
            cls.objects
            .filter(
                contratista=contratista,
                trabajo=trabajo,
                vigente_desde__lte=fecha
            )
            .filter(
                Q(vigente_hasta__gte=fecha) |
                Q(vigente_hasta__isnull=True)
            )
            .order_by("-vigente_desde")
            .first()
        )

    class Meta:
        unique_together = ("contratista", "trabajo", "precio", "vigente_desde", "vigente_hasta")
        indexes = [
            models.Index(fields=["contratista", "trabajo", "vigente_desde"]),
        ]


class ContratistaTrabajo(models.Model):
    contratista = models.ForeignKey(
        Contratista,
        on_delete=models.CASCADE,
        related_name="trabajos"
    )
    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.CASCADE
    )

    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("contratista", "trabajo")


class Obra(models.Model):
    nombre = models.CharField(max_length=100)
    etapa = models.CharField(max_length=100)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    razon_social = models.ForeignKey(RazonSocial, on_delete=models.CASCADE, related_name='obras')
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} | {self.etapa}"


class TipoAgrupador(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


class Agrupador(models.Model):
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="agrupadores"
    )

    tipo = models.ForeignKey(
        TipoAgrupador,
        on_delete=models.PROTECT,
        related_name="agrupadores"
    )

    numero = models.PositiveIntegerField()
    estructura = models.ForeignKey(
        Estructura,
        on_delete=models.CASCADE,
        related_name="agrupadores"
    )

    cantidad_viviendas = models.PositiveIntegerField()

    class Meta:
        unique_together = ("obra", "tipo", "numero")
        ordering = ["tipo__nombre", "numero"]

    def generar_viviendas(self, overwrite=False):
        with transaction.atomic():
            if overwrite:
                self.viviendas.all().delete()

            existentes = set(
                self.viviendas.values_list("numero", flat=True)
            )

            nuevas = []
            for i in range(1, self.cantidad_viviendas + 1):
                if i not in existentes:
                    nuevas.append(
                        Vivienda(
                            agrupador=self,
                            numero=i,
                            estructura=self.estructura
                        )
                    )

            Vivienda.objects.bulk_create(nuevas)

            for vivienda in nuevas:
                vivienda.generar_estados_trabajo()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.generar_viviendas()

    def __str__(self):
        return f"{self.tipo.codigo}-{self.numero} | {self.estructura}"


class Vivienda(models.Model):
    agrupador = models.ForeignKey(
        Agrupador,
        on_delete=models.CASCADE,
        related_name="viviendas"
    )

    numero = models.PositiveIntegerField()
    estructura = models.ForeignKey(
        Estructura,
        on_delete=models.PROTECT
    )

    class Meta:
        unique_together = ("agrupador", "numero")
        ordering = ["numero"]

    @property
    def esta_completa(self):
        return True if self.porcentaje_completado == 100 else False

    @property
    def porcentaje_completado(self) -> int:
        qs = self.estados_trabajo.all()

        total = qs.count()
        if total == 0:
            return 0

        completados = qs.filter(
            estado__in=[
                'realizado',
                'pagado',
                'no aplica',
            ]
        ).count()

        return round((completados / total) * 100)

    def generar_estados_trabajo(self):
        trabajos = (
            Trabajo.objects
            .filter(estructuratrabajo__estructura=self.estructura)
        )

        estados = [
            EstadoTrabajoVivienda(
                vivienda=self,
                trabajo=trabajo,
                estado="pendiente" if trabajo.es_unitario else "no_aplica"
            )
            for trabajo in trabajos
        ]

        EstadoTrabajoVivienda.objects.bulk_create(estados)

    def __str__(self):
        return f"Viv {self.numero} | {self.agrupador} | {self.estructura}"


class EstadoTrabajoVivienda(models.Model):
    ESTADOS = (
        ("pendiente", "Pendiente"),
        ("por_realizar", "Por realizar"),
        ("realizado", "Realizado"),
        ("pagado", "Pagado"),
        ("no_aplica", "No aplica"),
    )

    vivienda = models.ForeignKey(
        Vivienda,
        on_delete=models.CASCADE,
        related_name="estados_trabajo"
    )

    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.PROTECT
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendiente"
    )

    @property
    def estado_abreviatura(self):
        if self.estado == "pendiente":
            return ""
        if self.estado == "por_realizar":
            return ""
        if self.estado == "realizado":
            return "x"
        if self.estado == "pagado":
            return "1"
        if self.estado == "no_aplica":
            return "na"
        return "nf"

    class Meta:
        unique_together = ("vivienda", "trabajo")


class FolioDestajo(models.Model):
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)


class Destajo(models.Model):
    ESTADOS = (
        ['borrador', 'BORRADOR'],
        ['publicado', 'PUBLICADO'],
        ['cancelado', 'CANCELADO'],
    )

    folio = models.CharField(max_length=100, unique=True)
    folio_consecutivo = models.PositiveIntegerField()

    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")

    agrupador = models.ForeignKey(
        Agrupador,
        on_delete=models.PROTECT,
        related_name="destajos"
    )

    contratista = models.ForeignKey(
        Contratista,
        on_delete=models.PROTECT,
        related_name="destajos"
    )

    fecha = models.DateField(auto_now_add=True)

    solicitante = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="destajos_solicitados"
    )

    autoriza = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="destajos_autorizados"
    )

    observaciones = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            current_year = now().year

            with transaction.atomic():
                folio_control, _ = FolioDestajo.objects.select_for_update().get_or_create(
                    year=current_year,
                )

                folio_control.last_number += 1
                self.folio_consecutivo = folio_control.last_number

                self.folio = f"DESTAJO-{current_year}-{str(self.folio_consecutivo).zfill(5)}"

                folio_control.save()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return self.folio


class DestajoDetalle(models.Model):
    destajo = models.ForeignKey(
        Destajo,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.PROTECT
    )

    fecha_entrega = models.DateField(blank=True, null=True)

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unidad = models.CharField(
        max_length=50,
        choices=UNIDADES,
        default="vivienda"
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    surtido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        unique_together = ("destajo", "trabajo")

    @property
    def subtotal(self):
        return self.cantidad * self.precio

    @property
    def total(self):
        return self.subtotal

    def clean(self):
        super().clean()

        manzana = self.destajo.agrupador
        estructura = self.destajo.agrupador.estructura

        estructura_trabajo = EstructuraTrabajo.objects.filter(
            estructura=estructura,
            trabajo_id=self.trabajo_id
        ).first()

        if not estructura_trabajo:
            raise ValidationError({
                "trabajo": "Trabajo fuera del presupuesto",
            })

        cantidad_presupuestada = estructura_trabajo.cantidad_base
        cantidad_maxima = cantidad_presupuestada * Decimal(manzana.cantidad_viviendas)

        cantidad_usada = (
                DestajoDetalle.objects
                .filter(
                    destajo__manzana=manzana,
                    trabajo=self.trabajo
                )
                .exclude(pk=self.pk)
                .aggregate(total=Sum("cantidad"))
                ["total"] or Decimal("0")
        )

        cantidad_resultante = cantidad_usada + (self.cantidad or 0)

        if cantidad_resultante > cantidad_maxima:
            raise ValidationError({
                "cantidad": (
                    f"La cantidad solicitada excede el presupuesto.\n"
                    f"Presupuestado: {cantidad_maxima}\n"
                    f"Usado: {cantidad_usada}\n"
                    f"Disponible: {cantidad_maxima - cantidad_usada}"
                )
            })

        # Validar precio
        precio_catalogo = PrecioContratista.precio_vigente(
            contratista=self.destajo.contratista,
            trabajo=self.trabajo,
            fecha=self.destajo.fecha
        )

        if precio_catalogo is None:
            raise ValidationError(
                f"No se encontró precio para el trabajo {self.trabajo} del contratista {self.destajo.contratista}"
            )

        if precio_catalogo and self.precio != precio_catalogo.precio:
            raise ValidationError(
                "El precio no coincide con el catálogo vigente."
            )
