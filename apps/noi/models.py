from django.contrib.auth.models import User
from django.db import models

class Permiso(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = (
            ('acceder_modulo_noi', 'Acceder al Módulo de NOI'),
            ('ver_reporte_nomina_personal_noi', 'Ver reporte de Nomina y Personal NOI'),
            ('exportar_reporte_nomina_personal_noi', 'Exportar reporte de Nomina y Personal NOI'),
        )



class EmpresaNOI(models.Model):
    nombre_corto = models.CharField(max_length=50, unique=True, help_text="Ej: abocosa")
    razon_social = models.CharField(max_length=150)
    numero_empresa = models.CharField(max_length=5, help_text="Ej: 08")

    db_host = models.CharField(max_length=100, default="localhost")
    db_path = models.CharField(max_length=255)

    usuarios_permitidos = models.ManyToManyField(
        User,
        blank=True,
        related_name="empresas_noi_permitidas",
        help_text="Usuarios que tienen acceso a los datos de esta empresa."
    )

    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.razon_social} ({self.numero_empresa})"

    class Meta:
        verbose_name = 'EmpresaNOI'
        verbose_name_plural = 'EmpresasNOI'
        ordering = ['numero_empresa']
