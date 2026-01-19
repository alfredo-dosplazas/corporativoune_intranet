from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
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
        on_delete=models.PROTECT,
        related_name="requisiciones_papeleria_solicitante",
    )
    aprobador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="requisiciones_papaleria_aprobador",
    )
    compras = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="requisiciones_papeleria_compras",
    )
    contraloria = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="requisiciones_papeleria_contraloria",
    )

    creada_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="requisiciones_papeleria_creada_por",
    )

    estado = models.CharField(max_length=255, choices=ESTADOS_CHOICES, default="borrador")

    aprobo_solicitante = models.BooleanField(default=False)
    aprobo_aprobador = models.BooleanField(default=False)
    aprobo_compras = models.BooleanField(default=False)
    aprobo_contraloria = models.BooleanField(default=False)

    rechazador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="requisiciones_papeleria_rechazador",
    )
    razon_rechazo = models.TextField(blank=True, null=True, verbose_name='Razón de rechazo')

    fecha_autorizacion_contraloria = models.DateTimeField(blank=True, null=True)
    autorizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="requisiciones_papeleria"
    )

    es_papeleria_stock = models.BooleanField(
        default=False,
        help_text="Si se activa, la requisición se enviará directamente a Compras sin pasar por el aprobador del área.",
        verbose_name="¿Es papelería de stock?"
    )

    notas = models.TextField(blank=True, null=True, verbose_name="Notas Generales")

    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    @property
    def estado_ui(self):
        return {
            "borrador": {"label": "Borrador", "color": "badge-neutral"},
            "confirmada": {"label": "Confirmada", "color": "badge-info"},
            "enviada_aprobador": {"label": "En aprobación", "color": "badge-warning"},
            "autorizada_aprobador": {"label": "Aprobada por Aprobador", "color": "badge-success"},
            "enviada_compras": {"label": "En Compras", "color": "badge-warning"},
            "autorizada_compras": {"label": "Aprobada por Compras", "color": "badge-success"},
            "enviada_contraloria": {"label": "En Contraloría", "color": "badge-warning"},
            "autorizada_contraloria": {"label": "Autorizada por Contraloría", "color": "badge-success"},
            "esperando_entrega_articulo": {"label": "Esperando entrega", "color": "badge-accent"},
            "completada": {"label": "Completada", "color": "badge-success"},
            "cancelada": {"label": "Cancelada", "color": "badge-error"},
        }.get(self.estado, {"label": self.estado, "color": "badge-neutral"})

    @property
    def total(self):
        return sum([dr.subtotal for dr in self.detalle_requisicion.all()])

    def get_absolute_url(self):
        return reverse('papeleria:requisiciones__detail', args=(self.pk,))

    def puede_ver(self, usuario: User):
        if usuario.is_superuser:
            return True

        return usuario in [self.solicitante, self.aprobador, self.compras, self.contraloria]

    def puede_editar(self, user):
        if user.is_superuser:
            return True
        if user == self.solicitante and self.estado == "borrador":
            return True
        return False

    def puede_confirmar(self, user):
        if user.is_superuser and self.estado == 'borrador':
            return True
        if user == self.solicitante and self.estado == 'borrador':
            return True
        return False

    def puede_enviar_al_aprobador(self, user):
        if user.is_superuser and self.estado == 'confirmada':
            return True
        if user == self.solicitante and self.estado == 'confirmada':
            return True
        return False

    def puede_aprobar(self, user):
        if user.is_superuser and self.estado in ['enviada_aprobador', 'enviada_compras']:
            return True
        if user == self.aprobador and self.estado == "enviada_aprobador":
            return True
        if user == self.compras and self.estado == "enviada_compras":
            return True
        return False

    def puede_cancelar(self, user):
        if user.is_superuser and self.estado in ['borrador', 'confirmada', 'enviada_aprobador', 'autorizada_aprobador',
                                                 'enviada_compras', 'autorizada_compras', 'enviada_contraloria',
                                                 'autorizada_contraloria']:
            return True
        if user == self.solicitante and self.estado == "borrador":
            return True
        if user == self.aprobador and self.estado == "enviada_aprobador":
            return True
        if user == self.compras and self.estado == "enviada_compras":
            return True
        if user == self.contraloria and self.estado == "enviada_contraloria":
            return True
        return False

    def puede_autorizar(self, user):
        if user.is_superuser and self.estado == 'enviada_contraloria':
            return True
        if user == self.contraloria and self.estado == 'enviada_contraloria':
            return True
        return False

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
        ordering = ["-created_at"]
        verbose_name = "Requisición"
        verbose_name_plural = "Requisiciones"
        permissions = [
            ("aprobar_requisicion", "Aprobar Requisiciones"),
            ("cancelar_requisicion", "Cancelar o Rechazar Requisiciones"),
            ("enviar_requisicion_contraloria", "Envíar requisiciones aprobadas por compras a contraloría"),
            ("autorizar_requisicion", "Autorizar Requisiciones (Contraloría)"),
        ]


class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(
        Requisicion, on_delete=models.CASCADE, related_name="detalle_requisicion"
    )
    articulo = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name="detalle_requisicion"
    )
    cantidad = models.PositiveIntegerField()
    cantidad_autorizada = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)

    @property
    def cantidad_pendiente(self):
        return self.cantidad - self.cantidad_autorizada

    @property
    def subtotal(self):
        if self.cantidad_autorizada > 0:
            return self.cantidad_autorizada * self.articulo.importe
        if self.cantidad:
            return self.cantidad * self.articulo.importe
        return 0

    def __str__(self):
        return f"Detalle Requisición {self.requisicion} | {self.articulo} x {self.cantidad} : {self.cantidad_autorizada}"

    class Meta:
        unique_together = ["requisicion", "articulo"]


class ActividadRequisicion(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name="actividad_requisicion")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="actividad_requisicion")
    created_at = models.DateTimeField(auto_now_add=True)
    contenido = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Actividad {self.usuario} en {self.created_at}"

    class Meta:
        ordering = ["-created_at"]
