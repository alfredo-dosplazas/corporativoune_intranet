from django.db import models


class SAE(models.Model):
    """
    Modelo no gestionado por el ORM de Django (sin tabla en BD)
    utilizado únicamente para registrar los permisos personalizados del módulo SAE.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('view_sae', 'Puede ver el índice/módulo SAE'),
            ('view_inventario', 'Puede ver el reporte de inventario por almacén'),
            ('view_inventario_gerencia', 'Puede ver el reporte de inventario para gerencia'),
        ]