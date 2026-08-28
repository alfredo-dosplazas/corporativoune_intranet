from django.db import models


class Cuenta(models.Model):
    nombre = models.CharField(max_length=100)
    numero_cuenta_coi = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
