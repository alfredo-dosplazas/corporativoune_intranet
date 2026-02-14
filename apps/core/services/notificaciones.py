from apps.core.models import EmpresaSoporteSistemas
from apps.core.tasks import enviar_correo_task
from apps.directorio.models import Contacto
from apps.slack.tasks import enviar_slack_task


def notificar_soporte(
        empresa,
        subject: str,
        text_content: str | None = None,
        html_content: str | None = None,
        template_name_email: str | None = None,
        template_name_slack: str | None = None,
        context: dict | None = None,
        attachments: list | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        from_email: str | None = None,
):
    config: EmpresaSoporteSistemas | None = getattr(empresa, "config_soporte", None)

    if subject is None:
        subject = "Solicitud de Soporte desde Intranet del Corporativo"

    if not config or not config.activo:
        return

    if config.notificar_por_correo and config.correo_soporte:
        enviar_correo_task.delay(
            subject=subject,
            to=[config.correo_soporte],
            text_content=text_content,
            html_content=html_content,
            template_name=template_name_email,
            context=context,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            from_email=from_email,
        )

    if config.notificar_por_slack and config.slack_channel:
        enviar_slack_task.delay(config.slack_channel, text_content, template_name=template_name_slack, context=context)
