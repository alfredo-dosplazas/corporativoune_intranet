import ipaddress
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from apps.core.models import Empresa
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.slack.client import SlackClient


def rename_contacto_image(instance, filename):
    ext = filename.split(".")[-1]
    empresa = instance.empresa
    new_filename = f"{instance.nombre_completo}{f'_{instance.numero_empleado}' or ''}.{ext}"
    return os.path.join(f"{empresa.slug}/directorio/contactos/", new_filename)


class EmailContacto(models.Model):
    contacto = models.ForeignKey(
        "Contacto", on_delete=models.CASCADE, related_name="emails"
    )
    email = models.EmailField()
    es_principal = models.BooleanField(default=False)
    esta_activo = models.BooleanField(default=False)

    class Meta:
        unique_together = ("contacto", "email")


class TelefonoContacto(models.Model):
    contacto = models.ForeignKey(
        "Contacto", on_delete=models.CASCADE, related_name="telefonos"
    )
    telefono = models.CharField(max_length=11)
    extension = models.PositiveIntegerField(blank=True, null=True)
    es_principal = models.BooleanField(default=False)
    esta_activo = models.BooleanField(default=False)
    es_celular = models.BooleanField(default=False)

    class Meta:
        unique_together = ("contacto", "telefono", "extension")


class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class SedeIPRange(models.Model):
    sede = models.ForeignKey(
        Sede,
        on_delete=models.CASCADE,
        related_name="allowed_networks"
    )

    cidr = models.CharField(max_length=50)

    activa = models.BooleanField(default=True)

    def contiene_ip(self, ip):
        return ipaddress.ip_address(ip) in ipaddress.ip_network(self.cidr)


class Contacto(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, related_name="contacto")

    foto = models.ImageField(upload_to=rename_contacto_image, blank=True, null=True)

    numero_empleado = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
        verbose_name='Número De Empleado'
    )

    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True, null=True)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True)

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="contactos",
        help_text="Empresa en la que está dado de alta administrativamente (nómina).",
    )
    empresas_relacionadas = models.ManyToManyField(
        Empresa,
        blank=True,
        related_name='contactos_empresas_relacionadas',
        help_text="Empresas adicionales con las que este contacto tiene relación."
    )

    # DONDE SE GESTIONA
    sede_administrativa = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        related_name="contactos_administrados",
        help_text="Sede responsable del alta y gestión del contacto",
        blank=True,
        null=True,
    )

    # DONDE APARECE
    sedes_visibles = models.ManyToManyField(
        Sede,
        related_name="contactos_visibles",
        blank=True,
        help_text="Sedes donde este contacto aparece en el directorio"
    )

    jefe_directo = models.ForeignKey(
        "Contacto",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="a_cargo_de",
    )

    area = models.ForeignKey(Area, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Área',
                             related_name='contactos')
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Puesto',
                               related_name='contactos')

    fecha_nacimiento = models.DateField(blank=True, null=True)

    fecha_ingreso = models.DateField(blank=True, null=True)
    fecha_egreso = models.DateField(blank=True, null=True)

    email_slack = models.EmailField(
        blank=True, null=True, help_text="Correo Electrónico registrado en Slack."
    )
    slack_id = models.CharField(max_length=255, blank=True, null=True)

    mostrar_en_directorio = models.BooleanField(default=True, verbose_name='Mostrar en Directorio')
    mostrar_en_cumpleanios = models.BooleanField(default=True, verbose_name='Mostrar en Cumpleaños')

    @property
    def iniciales(self):
        return self.primer_nombre[0] + self.primer_apellido[0]

    @property
    def nombre_completo(self):
        return " ".join(
            filter(
                None,
                [
                    self.primer_nombre,
                    self.segundo_nombre,
                    self.primer_apellido,
                    self.segundo_apellido,
                ],
            )
        )

    @property
    def email_principal(self):
        return (
            self.emails
            .filter(es_principal=True, esta_activo=True)
            .first()
        )

    @property
    def emails_secundarios(self):
        return (
            self.emails
            .filter(es_principal=False, esta_activo=True)
        )

    @property
    def telefono_principal(self):
        return (
            self.telefonos
            .filter(es_principal=True, esta_activo=True)
            .first()
        )

    @property
    def telefonos_secundarios(self):
        return (
            self.telefonos
            .filter(es_principal=False, esta_activo=True)
        )

    @property
    def slack_url(self):
        return f"slack://user?team={settings.SLACK_TEAM_ID}&id={self.slack_id}"

    def json(self):
        return {
            'nombre_completo': self.nombre_completo,
            'numero_empleado': self.numero_empleado,
            'empresa': self.empresa.nombre if self.empresa else None,
            'area': self.area.nombre if self.area else None,
            'puesto': self.puesto.nombre if self.puesto else None,
            'sede_administrativa': self.sede_administrativa.nombre if self.sede_administrativa else None,
            'email_principal': self.email_principal.email if self.email_principal else None,
            'telefono_principal': self.telefono_principal.telefono if self.telefono_principal else None,
            'telefono_principal__extension': self.telefono_principal.extension if self.telefono_principal else None

        }

    def save(self, *args, **kwargs):
        if self.slack_id is None and self.email_slack:
            self.slack_id = SlackClient().get_slack_id_by_email(self.email_slack)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_completo}"

    class Meta:
        ordering = [
            "empresa__nombre_corto",
            "primer_nombre",
            "segundo_nombre",
            "primer_apellido",
            "segundo_apellido",
        ]
        permissions = [
            ('acceder_directorio', 'Acceder al Directorio'),
        ]
