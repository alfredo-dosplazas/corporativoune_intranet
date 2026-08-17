import logging
from apps.slack.models import ListaNotificacionSlack
from apps.slack.tasks import enviar_slack_task

logger = logging.getLogger(__name__)


def enviar_notificacion_evidencia_moldes(archivos_guardados, usuario, ruta_obra, url_carpeta):
    logger.info("Notificando evidencia moldes")

    lista = ListaNotificacionSlack.objects.get(nombre='EVIDENCIAS MOLDES')
    destinatarios = lista.destinatarios.filter(activo=True)

    total_archivos = len(archivos_guardados)

    # Mostrar hasta 5 nombres en la lista y resumir el resto si son más
    nombres_archivos = [f"`{a.name}`" for a in archivos_guardados[:5]]
    if total_archivos > 5:
        nombres_archivos.append(f"_...y {total_archivos - 5} más_")

    lista_archivos_str = "\n  • ".join(nombres_archivos)

    mensaje_slack = (
        f"📸 *Nuevas evidencias de moldes subidas ({total_archivos})*\n\n"
        f"• *Obra/Ruta:* `{ruta_obra}`\n"
        f"• *Usuario:* {usuario}\n"
        f"• *Cantidad:* {total_archivos} archivo(s)\n"
        f"• *Archivos:*\n  • {lista_archivos_str}\n\n"
        f"📂 <{url_carpeta}|*Hacer clic aquí para ver la carpeta de evidencias*>"
    )

    for destino in destinatarios:
        enviar_slack_task.delay(
            user_id=destino.usuario_slack.slack_id,
            mensaje=mensaje_slack,
        )

    logger.info("Evidencias de moldes notificadas!")