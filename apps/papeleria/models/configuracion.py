from django.contrib.auth.models import User
from django.db import models

from apps.core.models import Empresa


class ConfiguracionEmpresaPapeleria(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='configuracion_papeleria')
    compras = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compras_configuracion_papeleria')
    contraloria = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contraloria_configuracion_papeleria')

    def __str__(self):
        return f"Configuración de papelería: {self.empresa}"
