import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from apps.core.models import Empresa
from apps.rrhh.models.areas import Area


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
    es_principal = models.BooleanField(default=False)
    esta_activo = models.BooleanField(default=False)

    class Meta:
        unique_together = ("contacto", "telefono")


class Contacto(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, related_name="contacto")

    foto = models.ImageField(upload_to=rename_contacto_image, blank=True, null=True)

    numero_empleado = models.CharField(
        max_length=255, blank=True, null=True, unique=True
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
        related_name="usuarios",
        help_text="Empresa en la que está dado de alta administrativamente (nómina).",
    )

    jefe_directo = models.ForeignKey(
        "Contacto",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="a_cargo_de",
    )

    area = models.ForeignKey(Area, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Área')

    extension = models.CharField(max_length=255, blank=True, null=True)

    fecha_nacimiento = models.DateField(blank=True, null=True)

    fecha_ingreso = models.DateField(blank=True, null=True)
    fecha_egreso = models.DateField(blank=True, null=True)

    email_slack = models.EmailField(
        blank=True, null=True, help_text="Correo Electrónico registrado en Slack."
    )
    slack_id = models.CharField(max_length=255, blank=True, null=True)

    mostrar_en_directorio = models.BooleanField(default=True)

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
    def telefono_principal(self):
        return (
            self.telefonos
            .filter(es_principal=True, esta_activo=True)
            .first()
        )

    @property
    def slack_url(self):
        return f"slack://user?team={settings.SLACK_TEAM_ID}&id={self.slack_id}"

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
