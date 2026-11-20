from django.db import models


class ServidorSMB(models.Model):
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo (ej. Servidor Principal FP, Servidor DP, Contabilidad)"
    )
    slug = models.SlugField(
        unique=True,
        help_text="Identificador único en la URL (ej. servidor-fp, servidor-dp)"
    )
    host = models.CharField(
        max_length=255,
        help_text="IP o FQDN del servidor (ej. 172.16.2.1 o dac-remoto.frescopack.local)"
    )
    activo = models.BooleanField(default=True)
    descubrir_shares_automatico = models.BooleanField(
        default=True,
        help_text="Lista todos los recursos compartidos del servidor automáticamente (excepto los marcados como ocultos)."
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Servidor SMB"
        verbose_name_plural = "Servidores SMB"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.host})"


class RecursoCompartido(models.Model):
    servidor = models.ForeignKey(
        ServidorSMB,
        on_delete=models.CASCADE,
        related_name="recursos"
    )
    nombre_share = models.CharField(
        max_length=150,
        help_text="Nombre exacto del recurso compartido en Windows"
    )
    alias_visible = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nombre amigable opcional para mostrar en la interfaz"
    )
    oculto = models.BooleanField(
        default=False,
        help_text="Oculta este recurso cuando el descubrimiento automático está activo"
    )

    class Meta:
        verbose_name = "Recurso Compartido"
        verbose_name_plural = "Recursos Compartidos"
        unique_together = ("servidor", "nombre_share")
        ordering = ["nombre_share"]

    def __str__(self):
        return f"\\\\{self.servidor.host}\\{self.nombre_share}"