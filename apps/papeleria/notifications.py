from apps.core.tasks import enviar_correo_task
from apps.papeleria.models.requisiciones import Requisicion
from apps.slack.tasks import enviar_slack_task


def notificar_solicitar_aprobacion(request, requisicion: Requisicion, aprobador):
    if aprobador.contacto.slack_id:
        mensaje = (
            "*Tienes una requisición pendiente de aprobación*\n"
            f"Requisición: #{requisicion.folio}\n"
            f"Solicitante: {requisicion.solicitante}\n"
            f"Monto: ${requisicion.total:,.2f}\n"
            f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|👉 Aprobar requisición>"
        )

        enviar_slack_task.delay(
            user_id=aprobador.contacto.slack_id,
            mensaje=mensaje,
        )

    if aprobador.contacto.email_principal:
        enviar_correo_task.delay(
            subject=f"Aprobación de requisición de papelería - {requisicion.folio}",
            to=[aprobador.contacto.email_principal.email],
            template_name="apps/papeleria/emails/requisicion/solicitud_aprobacion.html",
            context={
                "aprobador": aprobador.contacto.nombre_completo,
                "folio": requisicion.folio,
                "solicitante": requisicion.solicitante.contacto.nombre_completo,
                "empresa": requisicion.empresa.nombre,
                "fecha_solicitud": requisicion.created_at,
                "estado": requisicion.get_estado_display(),
                "total": requisicion.total,
                "detalles": [
                    {
                        "articulo": d.articulo.nombre,
                        "cantidad": d.cantidad,
                        "subtotal": d.subtotal,
                    }
                    for d in requisicion.detalle_requisicion.all()
                ],
                "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
            }
        )


def notificar_solicitar_aprobacion_compras(request, requisicion: Requisicion, compras):
    if compras.contacto.slack_id:
        mensaje = (
            "*Tienes una requisición pendiente de aprobación*\n"
            f"Requisición: #{requisicion.folio}\n"
            f"Solicitante: {requisicion.solicitante.contacto}\n"
            f"Monto: ${requisicion.total:,.2f}\n"
            f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|👉 Aprobar requisición>"
        )

        enviar_slack_task.delay(
            user_id=compras.contacto.slack_id,
            mensaje=mensaje,
        )

    if compras.contacto.email_principal:
        enviar_correo_task.delay(
            subject=f"Aprobación de requisición de papelería - {requisicion.folio}",
            to=[compras.contacto.email_principal.email],
            template_name="apps/papeleria/emails/requisicion/solicitud_aprobacion.html",
            context={
                "aprobador": compras.contacto.nombre_completo,
                "folio": requisicion.folio,
                "solicitante": requisicion.solicitante.contacto.nombre_completo,
                "empresa": requisicion.empresa.nombre,
                "fecha_solicitud": requisicion.created_at,
                "estado": requisicion.get_estado_display(),
                "total": requisicion.total,
                "detalles": [
                    {
                        "articulo": d.articulo.nombre,
                        "cantidad": d.cantidad,
                        "subtotal": d.subtotal,
                    }
                    for d in requisicion.detalle_requisicion.all()
                ],
                "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
            }
        )


def notificar_aprobacion_solicitante(request, requisicion: Requisicion, solicitante, usuario):
    if solicitante.contacto.slack_id:
        mensaje = (
            "✅ *Tu requisición fue aprobada*\n\n"
            f"*Requisición:* #{requisicion.folio}\n"
            f"*Aprobó:* {usuario.contacto}\n"
            f"*Monto:* ${requisicion.total:,.2f}\n\n"
            f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición>"
        )

        enviar_slack_task.delay(
            user_id=solicitante.contacto.slack_id,
            mensaje=mensaje,
        )

    if solicitante.contacto.email_principal:
        enviar_correo_task.delay(
            subject=f"Requisición de papelería aprobada - {requisicion.folio}",
            to=[solicitante.contacto.email_principal.email],
            template_name="apps/papeleria/emails/requisicion/solicitud_aprobada.html",
            context={
                "aprobador": usuario.contacto.nombre_completo,
                "folio": requisicion.folio,
                "solicitante": requisicion.solicitante.contacto.nombre_completo,
                "empresa": requisicion.empresa.nombre,
                "fecha_solicitud": requisicion.created_at,
                "estado": requisicion.get_estado_display(),
                "total": requisicion.total,
                "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
            }
        )


def notificar_nuevo_mensaje_requisicion(request, requisicion, usuarios):
    for usuario in usuarios:
        contacto = getattr(usuario, "contacto", None)
        if not contacto:
            continue

        if contacto.slack_id:
            mensaje = (
                "*Nuevo Mensaje en requisición*\n\n"
                f"*Requisición:* #{requisicion.folio}\n"
                f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición>"
            )

            enviar_slack_task.delay(
                user_id=contacto.slack_id,
                mensaje=mensaje,
            )

        if contacto.email_principal:
            enviar_correo_task.delay(
                subject=f"Nuevo mensaje en requisición de papelería - {requisicion.folio}",
                to=[contacto.email_principal.email],
                text_content=f"""
                Nuevo mensaje en requisición - {requisicion.folio}
                {request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición
                """,
            )
