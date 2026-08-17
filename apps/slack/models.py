from django.contrib.auth.models import User
from django.db import models

from apps.slack.client import SlackClient


class ListaNotificacionSlack(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class ConfiguracionUsuarioSlack(models.Model):
    email = models.EmailField()
    slack_id = models.CharField(max_length=100, unique=True, blank=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usuario_slack')

    def save(self, *args, **kwargs):
        contacto = getattr(self.usuario, 'contacto')
        contacto_slack_id = contacto.slack_id

        if not self.slack_id:
            if contacto_slack_id:
                self.slack_id = contacto_slack_id
            else:
                self.slack_id = SlackClient().get_slack_id_by_email(self.email)

        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario} - {self.email}"


class DestinatarioSlack(models.Model):
    list = models.ForeignKey(ListaNotificacionSlack, on_delete=models.CASCADE, related_name='destinatarios')
    usuario_slack = models.ForeignKey(ConfiguracionUsuarioSlack, on_delete=models.CASCADE,
                                      related_name='destinatarios_usuario_slack')

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario_slack} - {self.list}"

    class Meta:
        unique_together = ['list', 'usuario_slack']
