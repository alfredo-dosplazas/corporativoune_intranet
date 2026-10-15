import uuid

from django.db import models
from django.urls import reverse

from apps.core.models import Empresa
from apps.rrhh.models.sedes import Sede
from intranet import settings


class Evento(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Evento (Ej. Rifa Fin de Año Corporativo)")
    slug = models.SlugField(unique=True, max_length=250, help_text="Identificador único para URLs y WebSockets")

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='eventos', blank=True, null=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='eventos', blank=True, null=True)

    activo = models.BooleanField(default=True, verbose_name="Evento Activo")
    fecha_evento = models.DateTimeField(verbose_name="Fecha del Evento")

    def __str__(self):
        return f"{self.nombre} ({self.empresa or 'General'})"


class Regalo(models.Model):
    # Relación obligatoria con el Evento
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='regalos', verbose_name="Evento")

    codigo_qr = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    numero = models.IntegerField(
        verbose_name="Número de Boleto / Rifa")  # Ojo: ya no es globalmente unique=True, sino único por evento
    nombre = models.CharField(max_length=200, verbose_name="Premio / Regalo")
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
        # Un número de boleto puede repetirse en diferentes eventos, pero no dentro del mismo evento
        unique_together = ('evento', 'numero')

    def get_canjeo_url(self):
        return f'{settings.APP_URL}{reverse("regalos:canjear_regalo", args=[self.evento.slug, self.codigo_qr])}'

    def __str__(self):
        return f"[{self.evento.nombre}] Premio #{self.numero} - {self.nombre}"
