from django.db import models


class Empresa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(max_length=100, unique=True)
    abreviatura = models.CharField(max_length=100)
    codigo = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="empresas/logos/", blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre_corto"]


class Modulo(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    icono = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.CharField(max_length=255, blank=True, null=True,
                                help_text="papeleria.view_requisicion,fotos.view_foto")
    url_name = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
