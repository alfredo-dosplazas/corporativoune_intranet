from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.regalos.models import Regalo
from apps.regalos.tasks import descargar_imagen_regalo_task


@receiver(post_save, sender=Regalo)
def auto_descargar_imagen(sender, instance, created, **kwargs):
    """
    Cuando se crea un nuevo Regalo sin imagen, lanza la tarea de Celery.
    Se valida estrictamente 'created' y que no tenga imagen previa.
    """
    update_fields = kwargs.get('update_fields')
    if update_fields and 'imagen' in update_fields:
        return

    if created and not instance.imagen:
        descargar_imagen_regalo_task.delay(instance.pk, instance.nombre)