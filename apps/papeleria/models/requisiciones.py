from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

from apps.core.models import Empresa
from apps.papeleria.models.articulos import Articulo


class Requisicion(models.Model):
    ESTADOS_CHOICES = [
        ("borrador", "BORRADOR"),
        ("confirmada", "CONFIRMADA"),
        ("enviada_aprobador", "ENVÍADA AL APROBADOR"),
        ("autorizada_aprobador", "AUTORIZADA POR APROBADOR"),
        ("enviada_compras", "ENVIADA A COMPRAS"),
        ("autorizada_compras", "AUTORIZADA POR COMPRAS"),
        ("enviada_contraloria", "ENVIADA A CONTRALORÍA"),
        ("autorizada_contraloria", "AUTORIZADA POR CONTRALORÍA"),
        ("esperando_entrega_articulo", "ESPERANDO ENTREGA DE ARTÍCULO"),
        ("completada", "COMPLETADA"),
        ("cancelada", "CANCELADA"),
    ]

    folio = models.CharField(max_length=100, unique=True, editable=False)
    folio_consecutivo = models.PositiveIntegerField(editable=False)

    requisicion_relacionada = models.ForeignKey(
        "Requisicion",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="requisiciones_relacionadas",
    )

    solicitante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requisiciones_papeleria_solicitante",
    )
    aprobador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requisiciones_papaleria_aprobador",
    )
    compras = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requisiciones_papeleria_compras",
    )
    contraloria = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requisiciones_papeleria_contraloria",
    )

    estado = models.CharField(max_length=255, choices=ESTADOS_CHOICES, default="borrador")

    aprobo_solicitante = models.BooleanField(default=False)
    aprobo_aprobador = models.BooleanField(default=False)
    aprobo_compras = models.BooleanField(default=False)
    aprobo_contraloria = models.BooleanField(default=False)
    articulo_entregado = models.BooleanField(default=False)

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="requisiciones_papeleria"
    )

    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            current_year = now().year

            ultimo = (
                Requisicion.objects.filter(
                    created_at__year=current_year, empresa=self.empresa
                )
                .order_by("-folio_consecutivo")
                .first()
            )
            if ultimo:
                self.folio_consecutivo = ultimo.folio_consecutivo + 1
            else:
                self.folio_consecutivo = 1

            self.folio = f"REQ-PAPE-{self.empresa.codigo}-{current_year}-{str(self.folio_consecutivo).zfill(5)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.folio

    class Meta:
        ordering = ["empresa", "-created_at"]
        verbose_name = "Requisición"
        verbose_name_plural = "Requisiciones"


class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(
        Requisicion, on_delete=models.CASCADE, related_name="detalle_requisicion"
    )
    articulo = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name="detalle_requisicion"
    )
    cantidad = models.PositiveIntegerField()
    cantidad_liberada = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)

    @property
    def cantidad_pendiente(self):
        return self.cantidad - self.cantidad_liberada

    @property
    def subtotal(self):
        if self.cantidad_liberada > 0:
            return self.cantidad_liberada * self.articulo.importe
        return self.cantidad * self.articulo.importe

    def __str__(self):
        return f"Detalle Requisición {self.requisicion} | {self.articulo} x {self.cantidad}"

    class Meta:
        unique_together = ["requisicion", "articulo"]
