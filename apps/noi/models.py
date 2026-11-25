from django.contrib.auth.models import User
from django.db import models

from apps.core.models import RazonSocial, Empresa
from apps.rrhh.models.sedes import Sede


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

    razon_social_destino = models.ForeignKey(
        RazonSocial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas_noi",
        help_text="Razón social del catálogo core asociada a esta base NOI."
    )
    empresa_default = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas_noi_default",
        help_text="Empresa destino por defecto si el departamento no tiene mapeo específico."
    )
    sede_default = models.ForeignKey(
        Sede,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas_noi_default",
        help_text="Sede administrativa por defecto para contactos creados desde esta empresa NOI."
    )

    usuarios_permitidos = models.ManyToManyField(
        User,
        blank=True,
        related_name="empresas_noi_permitidas",
        help_text="Usuarios que tienen acceso a los datos de esta empresa."
    )

    activa = models.BooleanField(default=True)
    sincronizar_con_directorio = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.razon_social} ({self.numero_empresa})"

    class Meta:
        verbose_name = 'EmpresaNOI'
        verbose_name_plural = 'EmpresasNOI'
        ordering = ['numero_empresa']

class MapeoDepartamentoNOI(models.Model):
    empresa_noi = models.ForeignKey(
        EmpresaNOI,
        on_delete=models.CASCADE,
        related_name="mapeos_departamento",
        verbose_name="Empresa NOI"
    )
    departamento_noi = models.CharField(
        max_length=150,
        verbose_name="Departamento en NOI",
        help_text="Nombre (o clave) del departamento tal como aparece en NOI."
    )
    empresa_destino = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="mapeos_departamento_noi",
        verbose_name="Empresa Destino"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Mapeo de Departamento NOI"
        verbose_name_plural = "Mapeos de Departamentos NOI"
        unique_together = ("empresa_noi", "departamento_noi")
        ordering = ["empresa_noi", "departamento_noi"]

    def __str__(self):
        return f"{self.empresa_noi.nombre_corto}: {self.departamento_noi} -> {self.empresa_destino.nombre_corto}"