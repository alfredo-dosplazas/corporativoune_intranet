from celery import shared_task
from django.utils import timezone

from apps.asistencias.exports.registros_txt import exportar_a_archivo
from apps.asistencias.services.exportador_asistencias import descargar_nuevas_transacciones

import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def exportar_asistencias_task(self):
    ahora = timezone.now()

    logging.info('Descargando nuevas transacciones...')
    transacciones = descargar_nuevas_transacciones(
        end=ahora.strftime("%Y-%m-%d %H:%M:%S"),
    )

    logging.info('Exportar asistencias en archivo en CPU Asistencias...')
    total = exportar_a_archivo(transacciones)

    logger.info(f"Total de transacciones: {total}")

    return total
