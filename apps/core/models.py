import ipaddress

from django.db import models


class Permiso(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = (
            ('acceder_sistema_contratos', 'Acceder al Módulo de Sistema De Contratos'),
            ('generar_reporte_presupuestos_vs', 'Ver y Generar Excel del reporte de presupuestos del VS Control'),
        )


class RazonSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(max_length=100, null=True)
    abreviatura = models.CharField(max_length=100, null=True)
    prefijo = models.CharField(max_length=100, null=True)

    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

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

    @classmethod
    def get_default(cls):
        obj, _ = cls.objects.get_or_create(
            nombre='Inmobiliaria Dos Plazas',
            defaults={
                'nombre_corto': 'Dos Plazas',
                'abreviatura': 'DP',
                'codigo': 'DP',
                'theme': 'dos_plazas',
            },
        )
        return obj

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre_corto"]


class EmpresaSoporteSistemas(models.Model):
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name="config_soporte"
    )

    notificar_por_correo = models.BooleanField(default=True)
    notificar_por_slack = models.BooleanField(default=False)

    correo_soporte = models.EmailField(
        blank=True,
        null=True,
        help_text="Correo donde se recibirán notificaciones de tickets"
    )

    slack_channel = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID del canal de Slack"
    )

    activo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Soporte - {self.empresa.nombre}"

    class Meta:
        verbose_name = "Configuración Soporte Sistemas"
        verbose_name_plural = "Configuraciones Soporte Sistemas"


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
    permisos = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="papeleria.view_requisicion,fotos.view_foto"
    )
    url_name = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    es_publico = models.BooleanField(
        default=False,
        help_text="El módulo puede ser accedido por cualquier empresa aunque no esté activo"
    )
    permite_anonimo = models.BooleanField(
        default=False,
        help_text="Puede ser accedido sin iniciar sesión"
    )
    requiere_ip = models.BooleanField(
        default=False,
        help_text="Restringe la visibilidad y acceso según la IP del usuario"
    )

    def puede_acceder(self, request, empresa=None) -> bool:
        from apps.core.utils.network import get_client_ip

        # 1. Validación por Red / IP
        if self.requiere_ip:
            ip_cliente = get_client_ip(request)
            if not self.ip_permitida(ip_cliente):
                return False

        # 2. Validación de Autenticación
        user = request.user
        if not user.is_authenticated:
            return self.permite_anonimo

        # 3. Validación de Permisos (Usamos has_perms directamente)
        if self.permisos:
            permisos_list = [p.strip() for p in self.permisos.split(",") if p.strip()]
            if not user.has_perms(permisos_list):
                return False

        # 4. Visibilidad Pública por Empresa
        if self.es_publico:
            return True

        # 5. Validación por Empresa
        if empresa is None:
            return False

        return self.modulos_empresa.filter(empresa=empresa, activo=True).exists()

    def ip_permitida(self, ip_str: str) -> bool:
        """Verifica si la IP está dentro de los rangos asignados al módulo."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            rangos = self.allowed_networks.filter(activa=True)
            for rango in rangos:
                if ip_obj in ipaddress.ip_network(rango.cidr):
                    return True
            return False
        except ValueError:
            return False

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"


class ModuloIPRange(models.Model):
    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.CASCADE,
        related_name="allowed_networks"
    )
    cidr = models.CharField(max_length=50, help_text="Ej: 172.17.4.0/24 o 127.0.0.1/32")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.modulo.nombre} - {self.cidr}"
