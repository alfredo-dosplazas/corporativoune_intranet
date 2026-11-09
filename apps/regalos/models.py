import uuid

from django.db import models
from django.urls import reverse

from apps.core.models import Empresa
from apps.image_searcher.images import get_placeholder_image
from apps.rrhh.models.sedes import Sede
from intranet import settings


class Invitado(models.Model):
    evento = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='invitados', verbose_name="Evento")
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
