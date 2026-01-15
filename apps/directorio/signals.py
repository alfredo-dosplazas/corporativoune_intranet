import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.directorio.models import Contacto

logger = logging.getLogger("signals")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_contacto_usuario(sender, instance, created, **kwargs):
    logger.info(
        "Signal post_save User ejecutada | user_id=%s | created=%s",
        instance.id,
        created
    )

    Contacto.objects.update_or_create(
        usuario=instance,
        defaults={
            'primer_nombre': instance.first_name,
            'primer_apellido': instance.last_name,
        }
    )
