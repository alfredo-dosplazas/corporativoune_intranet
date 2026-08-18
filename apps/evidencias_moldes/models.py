from django.db import models


class Permiso(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = [
            ('acceder_explorador_direccion_obras', 'Acceder al explorador carpeta Dirección Obras'),
            ('ver_foto', 'Ver foto en módulo de evidencias moldes'),
            ('subir_evidencia', 'Subir evidencia en módulo de evidencias moldes'),
        ]
