import logging

from apps.slack.models import ListaNotificacionSlack
from apps.slack.tasks import enviar_slack_task

logger = logging.getLogger(__name__)


def enviar_notificacion_evidencia_moldes(archivo_destino, usuario, ruta_obra, url_carpeta):
    logger.info("Notificando evidencia moldes")

    lista = ListaNotificacionSlack.objects.get(nombre='EVIDENCIAS MOLDES')
    destinatarios = lista.destinatarios.filter(activo=True)

    mensaje_slack = (
        f"📸 *Nueva evidencia de moldes subida*\n\n"
        f"• *Obra/Ruta:* `{ruta_obra}`\n"
        f"• *Usuario:* {usuario}\n"
        f"• *Archivo:* `{archivo_destino.name}`\n\n"
        f"📂 <{url_carpeta}|*Hacer clic aquí para ver la carpeta de evidencias*>"
    )

    for destino in destinatarios:
        enviar_slack_task.delay(
            user_id=destino.usuario_slack.slack_id,
            mensaje=mensaje_slack,
        )

    logger.info("Evidencias de moldes notificadas!")
