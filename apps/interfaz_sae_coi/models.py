from django.db import models

class Permiso(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = (
            ('view_documentos', 'Ver Documentos Polizas'),
            ('add_poliza', 'Agregar Poliza en COI'),
        )

class Cuenta(models.Model):
    nombre = models.CharField(max_length=100)
    numero_cuenta_coi = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class DocumentoContabilizado(models.Model):
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADO_COI', 'Enviado a COI'),
        ('ERROR', 'Error en integración'),
    ]

    folio_sae = models.CharField(max_length=50, db_index=True)
    uuid_xml = models.CharField(max_length=36, db_index=True, blank=True, null=True)
    empresa_suffix = models.CharField(max_length=10)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')
    poliza_generada = models.CharField(max_length=50, blank=True, null=True)
    ejercicio = models.IntegerField(blank=True, null=True)
    periodo = models.IntegerField(blank=True, null=True)

    mensaje_error = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('folio_sae', 'empresa_suffix')

    def __str__(self):
        return f"{self.folio_sae} ({self.empresa_suffix}) - {self.status}"
