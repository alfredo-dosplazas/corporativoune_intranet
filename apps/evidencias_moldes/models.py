from django.db import models


class Permiso(models.Model):
    class Meta:
        managed = False

        permissions = [
            ('acceder_explorador_direccion_obras', 'Acceder al explorador carpeta Dirección Obras'),
            ('ver_foto', 'Ver foto en módulo de evidencias moldes'),
        ]
