from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.core.models import RazonSocial


class Equipo(models.Model):
    ESTADO_CHOICES = [
        ('NUEVO', 'Nuevo'),
        ('USADO', 'Usado'),
        ('DANIADO', 'Dañado / En Reparación'),
        ('BAJA', 'Dado de Baja'),
    ]

    empresa = models.CharField(max_length=100, default="Mi Empresa S.A. de C.V.")
    nombre = models.CharField(max_length=100, help_text="Ej. Laptop Dell Latitude 5420")
    numero_serie = models.CharField(max_length=100, unique=True)
    identificador_interno = models.CharField(max_length=50, unique=True, help_text="Tag de activo fijo o ID interno")
    estado_actual = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='USADO')

    # Control de ubicación / custodia física
    ubicacion_fisica_actual = models.CharField(
        max_length=150,
        blank=True,
        help_text="Ubicación física actual (ej. Almacén TI, Oficina 3B, En poder del empleado)"
    )

    def __str__(self):
        return f"{self.nombre} - {self.numero_serie} ({self.identificador_interno})"


class Resguardo(models.Model):
    ESTADO_RESGUARDO_CHOICES = [
        ('ACTIVO', 'Activo (En uso)'),
        ('DEVUELTO', 'Devuelto'),
        ('CANCELADO', 'Cancelado'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='resguardos')

    # Datos de entrega
    fecha_entrega = models.DateField(default=timezone.now)
    recibe_nombre = models.CharField(max_length=150, verbose_name="Nombre de quien recibe")
    recibe_puesto_area = models.CharField(max_length=150, verbose_name="Puesto y área")

    # Estado inicial al entregar
    estado_equipo_entrega = models.CharField(
        max_length=10,
        choices=[('NUEVO', 'Nuevo'), ('USADO', 'Usado')],
        default='USADO'
    )

    # Accesorios incluidos (Booleanos y campo libre)
    incluye_mouse = models.BooleanField(default=False)
    incluye_cargador = models.BooleanField(default=False)
    incluye_bateria = models.BooleanField(default=False)
    otros_accesorios = models.CharField(max_length=255, blank=True, help_text="Especificar otros accesorios")

    observaciones_entrega = models.TextField(blank=True)

    # Firmas y control digital
    firmado_digital = models.BooleanField(default=False,
                                          help_text="Indica si el resguardo ya fue firmado y devuelto escaneado")
    archivo_resguardo_firmado = models.FileField(
        upload_to='resguardos_firmados/%Y/%m/',
        blank=True,
        null=True,
        help_text="Documento PDF o imagen del formato firmado"
    )

    # Control de devolución
    estado_resguardo = models.CharField(max_length=15, choices=ESTADO_RESGUARDO_CHOICES, default='ACTIVO')
    fecha_devolucion = models.DateField(blank=True, null=True)
    estado_equipo_devolucion = models.CharField(max_length=255, blank=True,
                                                verbose_name="Estado del equipo al devolver")
    observaciones_devolucion = models.TextField(blank=True)

    # Personal que elabora/revisa/aprueba (liga con usuarios del sistema Django)
    elaboro = models.ForeignKey(User, on_delete=models.PROTECT, related_name='resguardos_elaborados')
    reviso_nombre = models.CharField(max_length=100, default="Especialista en DO")
    aprobo_nombre = models.CharField(max_length=100, default="Contralor")

    custodio_fisico_actual = models.CharField(
        max_length=100,
        blank=True,
        help_text="Persona o área que lo tiene resguardado físicamente en almacén/TI"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resguardo #{self.id} - {self.equipo.nombre} ({self.recibe_nombre})"


def evidencia_upload_path(instance, filename):
    return f'evidencias/resguardo_{instance.resguardo.id}/{filename}'


class EvidenciaResguardo(models.Model):
    resguardo = models.ForeignKey(Resguardo, on_delete=models.CASCADE, related_name='evidencias')
    imagen = models.ImageField(upload_to=evidencia_upload_path)
    descripcion = models.CharField(max_length=255, blank=True, help_text="Ej. Rayón en la carcasa, Pantalla intacta")
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidencia {self.id} - Resguardo #{self.resguardo.id}"
