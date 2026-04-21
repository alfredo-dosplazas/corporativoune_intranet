from datetime import datetime
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from apps.core.models import RazonSocial


class Proveedor(models.Model):
    nombre_completo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    contacto = models.CharField(max_length=100)
    email = models.EmailField()
    domicilio = models.TextField()
    rfc = models.CharField(max_length=13, verbose_name="RFC")
    condicion_pago = models.CharField(max_length=100, verbose_name="Condición de pago")

    def __str__(self):
        return self.nombre_completo


class OrdenFolio(models.Model):
    razon_social = models.ForeignKey(RazonSocial, on_delete=models.CASCADE, related_name='folios_orden')
    prefijo = models.CharField(max_length=10)
    folio_actual = models.PositiveIntegerField(default=0)

    @staticmethod
    def generar_folio(razon_social):
        with transaction.atomic():
            prefijo = razon_social.prefijo
            folio_obj = OrdenFolio.objects.select_for_update().first()

            if not folio_obj:
                folio_obj = OrdenFolio.objects.create(razon_social=razon_social, prefijo=prefijo, folio_actual=0)

            folio_obj.folio_actual += 1
            folio_obj.save()

            return f"{folio_obj.prefijo}-{folio_obj.folio_actual:06d}"

    def __str__(self):
        return f"{self.prefijo}-{self.folio_actual}"


class Orden(models.Model):
    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("APROBADA", "Aprobada"),
        ("CANCELADA", "Cancelada"),
    ]

    CFDI_CHOICES = [
        ("G01", "G01"),
        ("G02", "G02"),
        ("G03", "G03"),
        ("I01", "I01"),
        ("I02", "I02"),
        ("I03", "I03"),
        ("I04", "I04"),
        ("I05", "I05"),
        ("I06", "I06"),
        ("I07", "I07"),
        ("I08", "I08"),
        ("D01", "D01"),
        ("D02", "D02"),
        ("D03", "D03"),
        ("D04", "D04"),
        ("D05", "D05"),
        ("D06", "D06"),
        ("D07", "D07"),
        ("D08", "D08"),
        ("D09", "D09"),
        ("D10", "D10"),
        ("P01", "P01"),
    ]

    METODO_PAGO_CHOICES = [
        ("PPD", "PPD"),
        ("PUE", "PUE"),
    ]

    FORMA_PAGO_CHOICES = [
        ("01 Efectivo", "01 Efectivo"),
        ("02 Cheque", "02 Cheque"),
        ("03 Transferencia", "03 Transferencia"),
        ("04 Tarjet Crèdito", "04 Tarjet Crèdito"),
        ("05 Monedero Electrónico", "05 Monedero Electrónico"),
        ("06 Dinero Electrónico", "06 Dinero Electrónico"),
        ("08 Vales de Despensa", "08 Vales de Despensa"),
        ("12 Dación de Pago", "12 Dación de Pago"),
        ("13 Pago por subrogaciòn", "13 Pago por subrogaciòn"),
        ("14 Pago por consignación", "14 Pago por consignación"),
        ("17 Compensación", "17 Compensación"),
        ("23 Novación", "23 Novación"),
        ("24 Confusión", "24 Confusión"),
        ("25 Remisiòn de deuda", "25 Remisiòn de deuda"),
        ("26 Prescripciòn o Caducidad", "26 Prescripciòn o Caducidad"),
        ("27 A satisfacción del Acreedor", "27 A satisfacción del Acreedor"),
        ("28 Tarjeta de Débito", "28 Tarjeta de Débito"),
        ("29 Tarjeta de Servicios", "29 Tarjeta de Servicios"),
        ("30 Aplicación de anticipos", "30 Aplicación de anticipos"),
        ("31 Intermediario Pagos", "31 Intermediario Pagos"),
        ("99 Por definir", "99 Por definir"),
    ]

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name="ordenes",
    )

    solicitante = models.ForeignKey(
        'directorio.Contacto',
        on_delete=models.CASCADE,
        related_name="ordenes_solicitante",
    )

    autoriza = models.ForeignKey(
        'directorio.Contacto',
        on_delete=models.CASCADE,
        limit_choices_to={'usuario__groups__name': 'AUTORIZADORES'},
        related_name="ordenes_autorizador",
    )

    creada_por = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name="ordenes_creada_por",
    )

    folio = models.CharField(max_length=20, unique=True, blank=True, null=True)

    razon_social = models.ForeignKey(RazonSocial, on_delete=models.CASCADE, related_name='ordenes',
                                     verbose_name='Razón Social')

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR")

    uso_cfdi = models.CharField(max_length=10, choices=CFDI_CHOICES, verbose_name='Uso de CFDI')
    metodo_pago = models.CharField(max_length=3, choices=METODO_PAGO_CHOICES, verbose_name='Método de pago')
    forma_pago = models.CharField(max_length=100, choices=FORMA_PAGO_CHOICES, verbose_name='Forma de pago')
    utilizado_en = models.TextField(verbose_name='Para ser utilizado en')
    fecha_orden = models.DateField(default=timezone.now, blank=True, verbose_name='Fecha de la orden')
    fecha_entrega = models.DateField(verbose_name='Fecha de entrega')
    lugar_entrega = models.TextField(verbose_name='Lugar de entrega')

    retencion_isr = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Retención ISR')
    retencion_cedular = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                            verbose_name='Retención Cedular')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return sum(d.subtotal for d in self.detalle_orden.all())

    @property
    def iva(self):
        return self.subtotal * Decimal("0.16")

    @property
    def total_retenciones(self):
        return ((self.retencion_cedular / 100) * self.subtotal) + ((self.retencion_isr / 100) * self.subtotal)

    @property
    def total(self):
        return self.subtotal + self.iva - self.total_retenciones

    @property
    def total_letra(self):
        from num2words import num2words

        total = self.total
        entero = int(total)
        decimal = int(round((total - entero) * 100))

        letras = num2words(entero, lang='es').upper()

        return f"({letras} PESOS {decimal:02d}/100 M.N.)"

    @property
    def entrega_texto(self):
        if not self.fecha_entrega:
            return ""

        hoy = timezone.now().date()
        dias = (self.fecha_entrega - hoy).days

        if dias < 0:
            return f"vencida hace {abs(dias)} días"
        elif dias == 0:
            return f"entrega inmediata"
        elif dias == 1:
            return f"en 1 día"
        else:
            return f"en {dias} días"

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = OrdenFolio.generar_folio(self.razon_social)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.folio


class DetalleOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="detalle_orden")
    cantidad = models.PositiveIntegerField()
    descripcion = models.TextField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        if self.cantidad is None or self.precio_unitario is None:
            return 0
        return self.cantidad * self.precio_unitario
