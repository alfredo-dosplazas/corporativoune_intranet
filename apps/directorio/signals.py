import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.directorio.models import Contacto, EmailContacto

logger = logging.getLogger("signals")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_o_vincular_contacto_usuario(sender, instance, created, **kwargs):
    logger.info(
        "Signal post_save User ejecutada | user_id=%s | created=%s",
        instance.id,
        created
    )

    # Si el usuario no tiene email, no hacemos nada
    if not instance.email:
        return

    from .models import Contacto, EmailContacto

    with transaction.atomic():

        # Buscar si ya existe un EmailContacto con ese email
        email_contacto = EmailContacto.objects.select_related("contacto").filter(
            email__iexact=instance.email
        ).first()

        if email_contacto and email_contacto.contacto:

            contacto = email_contacto.contacto

            # Vincular usuario si aún no está vinculado
            if contacto.usuario_id != instance.id:
                contacto.usuario = instance

            # Completar nombre si está vacío
            if not contacto.primer_nombre:
                contacto.primer_nombre = instance.first_name

            if not contacto.primer_apellido:
                contacto.primer_apellido = instance.last_name

            contacto.save(update_fields=[
                "usuario",
                "primer_nombre",
                "primer_apellido"
            ])

        else:
            # No existe contacto previo → crear nuevo
            Contacto.objects.get_or_create(
                usuario=instance,
                defaults={
                    "primer_nombre": instance.first_name,
                    "primer_apellido": instance.last_name,
                }
            )
