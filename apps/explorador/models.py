from django.db import models

class Permission(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = (
            ('acceder_explorador', 'Acceder al Explorador de Archivos'),
        )