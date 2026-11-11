from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.codigos_qr.utils import generar_qr_base64


class EventoVotacion(models.Model):
    TIPOS_EVALUACION = (
        ("estrellas", "Escala de Estrellas (1-5)"),
        ("numerico", "Puntuación Numérica (Ej. 0-100)"),
        ("seleccion", "Selección Única / Radio"),
    )

    TEMATICAS = (
        ('halloween', 'Halloween / Disfraces'),
        ('navidad', 'Fiesta de Diciembre / Fin de Año'),
        ('corporativo', 'Estándar Corporativo / General'),
    )
    tematica = models.CharField(max_length=20, choices=TEMATICAS, default='corporativo')

    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text="Ej: Selecciona la temática que más te guste para nuestro evento"
    )
    imagen_fondo = models.ImageField(upload_to="votaciones/fondos/", blank=True, null=True)

    etiqueta_opciones = models.CharField(
        max_length=50,
        default="Opción",
        help_text="Ejemplo: 'Disfraz', 'Temática', 'Candidato', 'Plato'"
    )

    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    requiere_identificador = models.BooleanField(
        default=True,
        help_text="Pide número de empleado o correo para evitar duplicados",
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    restringir_por_red = models.BooleanField(
        default=False,
        help_text="Si está activo, solo se podrá votar desde las redes permitidas configuradas para este evento."
    )

    @property
    def qr_imagen(self):
        url = f'{settings.APP_URL}{reverse('votaciones:votar_evento', args=[self.pk])}'
        qr_base64 = generar_qr_base64(url)
        return f'data:image/png;base64,{qr_base64}'

    def ip_permitida(self, ip_str: str) -> bool:
        """Verifica si la IP está dentro de los rangos permitidos para este evento."""
        import ipaddress
        if not self.restringir_por_red:
            return True  # Si no requiere restricción, pasa cualquier IP

        try:
            ip_obj = ipaddress.ip_address(ip_str)
            rangos = self.allowed_networks.filter(activa=True)
            if not rangos.exists():
                return True  # Si no hay rangos definidos pero el flag está activo, decide si bloquear o permitir (por defecto permitimos si no hay reglas)
            for rango in rangos:
                if ip_obj in ipaddress.ip_network(rango.cidr):
                    return True
            return False
        except ValueError:
            return False

    def __str__(self):
        return self.titulo


class EventoIPRange(models.Model):
    evento = models.ForeignKey(
        EventoVotacion,
        on_delete=models.CASCADE,
        related_name="allowed_networks"
    )
    cidr = models.CharField(max_length=50, help_text="Ej: 172.17.4.0/24 o 127.0.0.1/32")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.evento.titulo} -> {self.cidr}"


class Criterio(models.Model):
    """Las categorías o preguntas a calificar (Ej: Creatividad, Vestimenta)"""

    evento = models.ForeignKey(
        EventoVotacion, on_delete=models.CASCADE, related_name="criterios"
    )
    texto = models.CharField(max_length=250)
    tipo = models.CharField(
        max_length=20,
        choices=EventoVotacion.TIPOS_EVALUACION,
        default="estrellas",
    )
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="Ponderación para el cálculo final",
    )

    def __str__(self):
        return f"{self.evento.titulo} - {self.texto}"


class OpcionParticipante(models.Model):
    """El participante, disfraz o equipo que está siendo evaluado"""

    evento = models.ForeignKey(
        EventoVotacion, on_delete=models.CASCADE, related_name="participantes"
    )
    nombre = models.CharField(max_length=200)
    imagen = models.ImageField(
        upload_to="concursos/", blank=True, null=True
    )  # Opcional para mostrar foto del disfraz
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class VotoSesion(models.Model):
    """Controla quién emitió los votos para bloquear duplicados en equipos compartidos"""

    evento = models.ForeignKey(EventoVotacion, on_delete=models.CASCADE)
    identificador = models.CharField(
        max_length=100,
        help_text="Número de empleado, correo o token generado",
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        # Un identificador solo puede votar una vez por evento
        unique_together = ("evento", "identificador")

    def __str__(self):
        return f"Voto de {self.identificador} en {self.evento.titulo}"


class DetalleVoto(models.Model):
    """El puntaje específico otorgado a cada participante en cada criterio"""

    sesion_voto = models.ForeignKey(
        VotoSesion, on_delete=models.CASCADE, related_name="detalles"
    )
    participante = models.ForeignKey(
        OpcionParticipante, on_delete=models.CASCADE
    )
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE)
    valor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Puntaje otorgado (Ej: 5 para estrella, 90 para numérico)",
    )

    def __str__(self):
        return f"{self.participante.nombre} -> {self.criterio.texto}: {self.valor}"
