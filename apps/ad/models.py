import base64
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet

User = get_user_model()


class CredencialADUsuario(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="credencial_ad",
        verbose_name="Usuario Django"
    )
    ad_username = models.CharField("Usuario AD", max_length=150)
    ad_domain = models.CharField("Dominio AD", max_length=150, default="TU_DOMINIO")
    _ad_password_encrypted = models.BinaryField("Contraseña Cifrada")

    def set_password(self, raw_password: str):
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        self._ad_password_encrypted = f.encrypt(raw_password.encode())

    def get_password(self) -> str:
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        return f.decrypt(bytes(self._ad_password_encrypted)).decode()

    def __str__(self):
        return f"Credencial AD ({self.ad_username}) - {self.usuario.username}"
