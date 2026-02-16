import ipaddress

from django.db import models

from apps.core.models import Empresa


class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    activa = models.BooleanField(default=True)

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="sedes",
    )

    @classmethod
    def get_default(cls):
        obj, _ = cls.objects.get_or_create(
            nombre='Corporativo UNE Celaya',
            defaults={
                'codigo': 'UNE-CELAYA',
                'ciudad': 'Celaya'
            }
        )

        return obj

    def __str__(self):
        return self.nombre


class SedeIPRange(models.Model):
    sede = models.ForeignKey(
        Sede,
        on_delete=models.CASCADE,
        related_name="allowed_networks"
    )

    cidr = models.CharField(max_length=50)

    activa = models.BooleanField(default=True)

    def contiene_ip(self, ip):
        return ipaddress.ip_address(ip) in ipaddress.ip_network(self.cidr)
