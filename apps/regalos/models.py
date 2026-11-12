import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.models import Empresa
from apps.image_searcher.images import get_placeholder_image
from apps.rrhh.models.sedes import Sede


class Invitado(models.Model):
    evento = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='invitados', verbose_name="Evento")

    categoria = models.ForeignKey(
        'CategoriaRegalo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitados',
        verbose_name="Categoría del Invitado"
    )

    codigo_qr = models.CharField(max_length=50, unique=True, default=uuid.uuid4, editable=False)
    primer_nombre = models.CharField(max_length=200)
    segundo_nombre = models.CharField(max_length=200, blank=True, null=True)
    primer_apellido = models.CharField(max_length=200)
    segundo_apellido = models.CharField(max_length=200, blank=True, null=True)

    foto = models.ImageField(upload_to='invitados', blank=True, null=True)

    asistio = models.BooleanField(default=False)

    @property
    def nombre_completo(self):
        return " ".join(
            filter(
                None,
                [
                    self.primer_nombre,
                    self.segundo_nombre,
                    self.primer_apellido,
                    self.segundo_apellido,
                ],
            )
        )

    class Meta:
        verbose_name = "Invitado"
        verbose_name_plural = "Invitados"
        unique_together = ('evento', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')
        ordering = ('primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')

    def __str__(self):
        return f"{self.nombre_completo} - {self.evento.nombre}"


class Evento(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Evento (Ej. Rifa Fin de Año Corporativo)")
    slug = models.SlugField(unique=True, max_length=250, help_text="Identificador único para URLs y WebSockets")

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='eventos', blank=True, null=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='eventos', blank=True, null=True)

    activo = models.BooleanField(default=True, verbose_name="Evento Activo")
    fecha_evento = models.DateTimeField(verbose_name="Fecha del Evento")

    def __str__(self):
        return f"{self.nombre} ({self.empresa or 'General'})"


class CategoriaRegalo(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='categorias', verbose_name="Evento")
    nombre = models.CharField(max_length=100, verbose_name="Nombre de Categoría")
    color = models.CharField(max_length=50, default="#3b82f6",
                             verbose_name="Color Identificador (Hex o Nombre)")

    class Meta:
        verbose_name = "Categoría de Regalo"
        verbose_name_plural = "Categorías de Regalos"
        ordering = ['nombre']
        unique_together = ['evento', 'nombre']

    def __str__(self):
        return f"{self.nombre}"


class Regalo(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='regalos', verbose_name="Evento")
    categoria = models.ForeignKey(CategoriaRegalo, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='regalos', verbose_name="Categoría")
    codigo_qr = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    numero = models.IntegerField(
        verbose_name="Número de Boleto / Rifa")
    nombre = models.CharField(max_length=200, verbose_name="Premio / Regalo")

    invitado = models.ForeignKey(Invitado, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='regalos_ganados')

    ganador_nombre = models.CharField(max_length=150, blank=True, null=True, editable=False)

    canjeado = models.BooleanField(default=False, editable=True)
    fecha_canje = models.DateTimeField(null=True, blank=True, editable=False)
    imagen = models.ImageField(upload_to='regalos', blank=True, null=True)
    destacado = models.BooleanField(
        default=False,
        verbose_name="Premio Destacado / Especial",
        help_text="Si está activo, se mostrará con un diseño especial al canjearse."
    )

    class Meta:
        unique_together = ('evento', 'numero')

    def get_canjeo_url(self):
        return f'{settings.APP_URL}{reverse("regalos:canjear_regalo", args=[self.evento.slug])}?regalo_qr={self.codigo_qr}'

    def __str__(self):
        return f"[{self.evento.nombre}] Premio #{self.numero} - {self.nombre}"


class CorridaSorteo(models.Model):
    """
    Registra cada ejecución o 'remezcla' del sorteo masivo de un evento.
    """
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='corridas_sorteo',
        verbose_name="Evento"
    )
    numero_corrida = models.PositiveIntegerField(
        verbose_name="Número de Ejecución / Mezcla",
        help_text="Consecutivo de veces que se ha ejecutado el sorteo para este evento (1, 2, 3...)"
    )
    ejecutado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ejecutado por"
    )
    fecha_ejecucion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora de Ejecución"
    )
    es_remezcla = models.BooleanField(
        default=False,
        verbose_name="¿Fue Remezcla?",
        help_text="Indica si esta corrida sobrescribió un sorteo previo."
    )
    es_actual = models.BooleanField(
        default=True,
        verbose_name="¿Es la Corrida Vigente?",
        help_text="Marca cuál es la corrida activa actualmente en las pantallas."
    )

    # Métricas e información de auditoría
    total_invitados_participantes = models.PositiveIntegerField(
        default=0,
        verbose_name="Invitados Participantes"
    )
    total_regalos_asignados = models.PositiveIntegerField(
        default=0,
        verbose_name="Regalos Asignados"
    )
    hash_integridad = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Hash SHA-256 de Verificación",
        help_text="Firma criptográfica del resultado para garantizar que no fue alterado."
    )
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP del Operador"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones / Motivo de remezcla"
    )

    class Meta:
        verbose_name = "Log de Corrida de Sorteo"
        verbose_name_plural = "Logs de Corridas de Sorteo"
        ordering = ['-numero_corrida', '-fecha_ejecucion']
        unique_together = ('evento', 'numero_corrida')

    def save(self, *args, **kwargs):
        # Si es nueva corrida, calcular consecutivo automático y marcar las anteriores como no vigentes
        if not self.pk:
            ultima = CorridaSorteo.objects.filter(evento=self.evento).order_by('-numero_corrida').first()
            self.numero_corrida = (ultima.numero_corrida + 1) if ultima else 1
            if self.numero_corrida > 1:
                self.es_remezcla = True

            if self.es_actual:
                CorridaSorteo.objects.filter(evento=self.evento, es_actual=True).update(es_actual=False)

        super().save(*args, **kwargs)

    def __str__(self):
        estado = "VIGENTE" if self.es_actual else "HISTÓRICO"
        return f"[{self.evento.nombre}] Corrida #{self.numero_corrida} ({estado}) - {self.fecha_ejecucion.strftime('%d/%m/%Y %H:%M')}"


class DetalleCorridaSorteo(models.Model):
    """
    Fotografía inmutable de cada asignación (Regalo -> Invitado) ocurrida en una corrida específica.
    """
    corrida = models.ForeignKey(
        CorridaSorteo,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Corrida de Sorteo"
    )
    regalo = models.ForeignKey(
        Regalo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Regalo"
    )
    invitado = models.ForeignKey(
        Invitado,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Invitado Ganador"
    )

    # Guardamos los valores planos por si en el futuro se edita/elimina el regalo o el invitado
    numero_regalo = models.IntegerField(verbose_name="Folio del Regalo")
    nombre_regalo = models.CharField(max_length=200, verbose_name="Nombre del Premio")
    categoria_nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Categoría")
    destacado = models.BooleanField(default=False, verbose_name="Fue Destacado")
    ganador_nombre = models.CharField(max_length=250, verbose_name="Nombre Completo del Ganador")

    class Meta:
        verbose_name = "Detalle de Asignación en Corrida"
        verbose_name_plural = "Detalles de Asignaciones en Corridas"
        ordering = ['numero_regalo']

    def __str__(self):
        return f"Corrida #{self.corrida.numero_corrida} | #{self.numero_regalo:03d} {self.nombre_regalo} -> {self.ganador_nombre}"
