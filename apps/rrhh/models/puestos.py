from django.db import models

from apps.core.models import Empresa


class Puesto(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='puesto')

    def __str__(self):
        return f'{self.nombre} ({self.empresa.nombre_corto})'
