from django.contrib.auth.models import User
from django.db import models

from apps.core.models import Empresa


class Area(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='areas')
    jefe_area = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='jefe_areas')

    aprobador_papeleria = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                            related_name="aprobador_papeleria_areas",
                                            help_text='Encargado de aprobar la papelería del área')

    def __str__(self):
        return f'{self.nombre}'

    class Meta:
        verbose_name_plural = "Áreas"
        verbose_name = "Área"
        ordering = ("empresa", "nombre")
        permissions = [
            ('acceder_rrhh', 'Acceder al módulo de RRHH'),
        ]

    @classmethod
    def get_default(cls, empresa=None):
        if empresa is None:
            empresa = Empresa.get_default()

        obj, _ = cls.objects.get_or_create(
            nombre='General',
            empresa=empresa
        )

        return obj
