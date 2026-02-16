from django.db import models

from apps.core.models import Empresa


class Puesto(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='puesto')

    def __str__(self):
        return f'{self.nombre}'

    class Meta:
        ordering = ("empresa", "nombre")

    @classmethod
    def get_default(cls, empresa=None):
        if empresa is None:
            empresa = Empresa.get_default()

        obj, _ = cls.objects.get_or_create(
            nombre='Asistente Administrativo',
            empresa=empresa
        )

        return obj
