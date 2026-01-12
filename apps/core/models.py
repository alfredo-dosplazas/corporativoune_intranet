from django.db import models


class Modulo(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    icono = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.CharField(max_length=255, blank=True, null=True, help_text="papeleria.view_requisicion,fotos.view_foto")
    url_name = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
