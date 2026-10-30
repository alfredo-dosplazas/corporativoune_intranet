from django.db import models

class EventoVotacion(models.Model):
    TIPOS_EVALUACION = (
        ("estrellas", "Escala de Estrellas (1-5)"),
        ("numerico", "Puntuación Numérica (Ej. 0-100)"),
        ("seleccion", "Selección Única / Radio"),
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    # Define si requiere identificación o es completamente anónimo libre
    requiere_identificador = models.BooleanField(
        default=True,
        help_text="Pide número de empleado o correo para evitar duplicados",
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.titulo


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