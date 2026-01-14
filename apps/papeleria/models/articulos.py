from django.db import models
from django.urls import reverse

from apps.core.models import Empresa


class Unidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    clave = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Unidades"


class Articulo(models.Model):
    imagen = models.ImageField(upload_to="papeleria/articulos/imagenes/", blank=True, null=True)
    codigo_vs_dp = models.CharField(
        verbose_name="Código VS DP", max_length=255, blank=True, null=True
    )
    numero_papeleria = models.CharField(
        verbose_name="Número Papelería", max_length=255, blank=True, null=True
    )
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    unidad = models.ForeignKey(
        Unidad, on_delete=models.CASCADE, related_name="articulos"
    )
    precio = models.DecimalField(decimal_places=4, max_digits=20, default=0)
    impuesto = models.DecimalField(decimal_places=4, max_digits=20, default=0.16)

    es_cuadro_basico = models.BooleanField(verbose_name="¿Pertenece al cuadro básico?")
    mostrar_en_sitio = models.BooleanField(
        default=True,
        help_text="Seleccionar para que este artículo se pueda ver y seleccionar en el módulo de papelería",
    )

    empresas = models.ManyToManyField(
        Empresa,
        blank=True,
        related_name="articulos",
        help_text="Que empresas pueden ver este artículo",
    )

    def get_absolute_url(self):
        return reverse('papeleria:articulos__detail', args=[self.id])

    def __str__(self):
        return self.nombre

    @property
    def importe(self):
        return self.precio * (1 + self.impuesto)

    class Meta:
        ordering = ["nombre"]
        permissions = [
            ("acceder_papeleria", "Acceder papelería")
        ]
