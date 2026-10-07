import uuid

from django.db import models
from django.urls import reverse

from intranet import settings


class Regalo(models.Model):
    codigo_qr = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    numero = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=200)
    ganador_nombre = models.CharField(max_length=150, blank=True, null=True, editable=False)
    canjeado = models.BooleanField(default=False, editable=True)
    fecha_canje = models.DateTimeField(null=True, blank=True, editable=False)

    imagen = models.ImageField(upload_to='regalos', blank=True, null=True)

    def get_canjeo_url(self):
        return f'{settings.APP_URL}{reverse('regalos:canjear_regalo', args=[self.codigo_qr])}'

    def __str__(self):
        return f"Premio #{self.numero} - {self.nombre}"
