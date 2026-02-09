import ipaddress

from django.db import models


class RazonSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(max_length=100, null=True)
    abreviatura = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Razones sociales"
        verbose_name = "Razón social"
        ordering = ['nombre']


class Empresa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(max_length=100, unique=True)
    abreviatura = models.CharField(max_length=100)
    codigo = models.CharField(max_length=100)
    theme = models.CharField(max_length=100, default='light')
    logo = models.ImageField(upload_to="empresas/logos/", blank=True, null=True)

    modulos = models.ManyToManyField(
        "Modulo",
        through="ModuloEmpresa",
        related_name="empresas",
        blank=True,
    )

    @property
    def slug(self):
        return self.nombre_corto.lower().replace(" ", "-")

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre_corto"]

class EmpresaIPRange(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="allowed_networks"
    )

    cidr = models.CharField(max_length=50)

    activa = models.BooleanField(default=True)

    def contiene_ip(self, ip):
        return ipaddress.ip_address(ip) in ipaddress.ip_network(self.cidr)

class ModuloEmpresa(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="modulos_empresa"
    )
    modulo = models.ForeignKey(
        "Modulo",
        on_delete=models.CASCADE,
        related_name="modulos_empresa"
    )
    activo = models.BooleanField(default=False)

    class Meta:
        unique_together = ("empresa", "modulo")


class Modulo(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    icono = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.CharField(max_length=255, blank=True, null=True,
                                help_text="papeleria.view_requisicion,fotos.view_foto")
    url_name = models.CharField(max_length=255)

    es_publico = models.BooleanField(
        default=False,
        help_text="El módulo puede ser accedido por cualquier empresa aunque no esté activo"
    )

    permite_anonimo = models.BooleanField(
        default=False,
        help_text="Puede ser accedido sin iniciar sesión"
    )

    def puede_acceder(self, request, empresa=None) -> bool:
        user = request.user

        if not user.is_authenticated:
            return self.permite_anonimo

        if self.permisos:
            permisos = [p.strip() for p in self.permisos.split(",")]
            if not user.has_perms(permisos):
                return False

        if self.es_publico:
            return True

        if empresa is None:
            return False

        return self.modulos_empresa.filter(
            empresa=empresa,
            activo=True
        ).exists()

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
