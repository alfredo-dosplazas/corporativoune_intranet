import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.papeleria.models.requisiciones import Requisicion, ActividadRequisicion

logger = logging.getLogger("signals")


@receiver(post_save, sender=Requisicion)
def crear_actividad_requisicion(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Creando actividad requisicion {instance}")
        usuario = instance.creada_por
        actividad_owner = str(getattr(usuario, "contacto", usuario.username))
        ActividadRequisicion.objects.create(
            usuario=usuario,
            requisicion=instance,
            tipo="system",
            contenido=f"{actividad_owner} creó la requisición",
        )
