from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

REGIMENES_CHOICES = [
    ('REGIMEN GENERAL DE LEY PERSONAS MORALES', 'REGIMEN GENERAL DE LEY PERSONAS MORALES'),
    ('PERSONAS FISICAS CON ACTIVIDAD EMPRESARIAL Y PROF', 'PERSONAS FISICAS CON ACTIVIDAD EMPRESARIAL Y PROF'),
    ('PERSONAS FISICAS CON ACTIVIDAD EMPRESARIAL Y PROF', 'PERSONAS FISICAS CON ACTIVIDAD EMPRESARIAL Y PROF'),
]

CONDICIONES_PAGO_CHOICES = [
    ('CONTADO', 'CONTADO'),
    ('CREDITO', 'CREDITO'),
    ('CREDITO 15 DÍAS', 'CREDITO 15 DÍAS'),
    ('CREDITO 30 DÍAS', 'CREDITO 30 DÍAS'),
]


class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    domicilio = models.TextField()
    ciudad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    codigo_postal = models.CharField(max_length=5)
    regimen = models.CharField(max_length=255, choices=REGIMENES_CHOICES, blank=False, null=False)
    telefono = models.TextField(blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    tipo_servicio = models.CharField(max_length=255)

    condiciones_pago = models.CharField(max_length=255, choices=CONDICIONES_PAGO_CHOICES)

    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class Equipo(models.Model):
    nombre = models.CharField(max_length=255)
    identificador = models.CharField(max_length=255, blank=True, null=True)
    serie = models.CharField(max_length=255, blank=True, null=True)
    marca = models.CharField(max_length=255, blank=True, null=True)
    operador = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre


class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('cancelado', 'Cancelado'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    estado = models.CharField(max_length=255, choices=ESTADO_CHOICES, default='borrador')

    fecha = models.DateField()

    clave = models.CharField(max_length=255)

    obra = models.CharField(max_length=255, blank=True, null=True)
    fraccionamiento = models.CharField(max_length=255, blank=True, null=True)

    creada_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes_compra', blank=True, null=True)

    impuesto_isr = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    impuesto_cedular = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return sum([d.total_partida for d in self.detalles.all()])

    @property
    def subtotal_isr(self):
        return self.subtotal * (self.impuesto_isr / 100)

    @property
    def subtotal_cedular(self):
        return self.subtotal * (self.impuesto_cedular / 100)

    @property
    def iva(self):
        return self.subtotal * Decimal(0.16)

    @property
    def total(self):
        retenciones = self.subtotal_isr + self.subtotal_cedular
        return self.subtotal + self.iva - retenciones

    def __str__(self):
        return self.clave

    class Meta:
        ordering = ['-fecha']


class DetalleOrdenCompra(models.Model):
    CONCEPTO_CHOICES = [
        ('servicio', 'Servicio'),
        ('refacciones', 'Refacciones'),
    ]

    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')

    descripcion = models.TextField()
    cantidad = models.PositiveIntegerField()
    unidad = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    equipo = models.CharField(max_length=255, blank=True, null=True)

    @property
    def total_partida(self):
        return self.cantidad * self.precio
