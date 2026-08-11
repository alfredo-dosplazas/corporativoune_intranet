from django.db import models


class Permisos(models.Model):
    class Meta:
        managed = False
        permissions = [
            ('acceder_explorador_direccion_obras', 'Acceder al explorador carpeta Dirección Obras')
        ]
