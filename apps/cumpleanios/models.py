from django.db import models
from django.utils.timezone import now

from apps.directorio.models import Contacto


class CumpleaneroManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(mostrar_en_cumpleanios=True)
        )


class Cumpleanero(Contacto):
    objects = CumpleaneroManager()

    @property
    def es_hoy(self):
        if not self.fecha_nacimiento:
            return False
        today = now().date()
        return (
                self.fecha_nacimiento.day == today.day and
                self.fecha_nacimiento.month == today.month
        )

    @property
    def edad_actual(self):
        if not self.fecha_nacimiento:
            return None
        today = now().date()
        return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) <
                (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    class Meta:
        proxy = True
        verbose_name = "Cumpleañero"
        verbose_name_plural = "Cumpleañeros"
