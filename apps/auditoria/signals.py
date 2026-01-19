import logging

from django.contrib.admin.models import LogEntry
from django.contrib.auth.signals import user_logged_in
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from apps.core.utils.network import get_client_ip
from .middleware import get_current_user, get_current_ip
from .models import UserAccessLog, AuditLog
from .utils import model_to_dict_simple

logger = logging.getLogger("auditoria.signals")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(
        "User login | user=%s | ip=%s",
        user.pk,
        get_client_ip(request),
    )

    UserAccessLog.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        path="LOGIN",
        method="AUTH",
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


EXCLUDED_MODELS = [
    AuditLog,
    UserAccessLog,
    LogEntry,
    ContentType,
]


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if sender in EXCLUDED_MODELS:
        return

    if not instance.pk:
        instance._old_data = None
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_data = model_to_dict_simple(old_instance)
    except sender.DoesNotExist:
        instance._old_data = None
    except Exception as e:
        logger.exception(
            "Error getting old_data | model=%s | pk=%s",
            sender.__name__,
            instance.pk,
        )
        instance._old_data = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if sender in EXCLUDED_MODELS:
        return

    action = "CREATE" if created else "UPDATE"

    logger.info(
        "%s | model=%s | pk=%s | user=%s | ip=%s",
        action,
        sender.__name__,
        instance.pk,
        get_current_user(),
        get_current_ip(),
    )

    try:
        AuditLog.objects.create(
            user=get_current_user(),
            ip_address=get_current_ip(),
            action=action,
            app_label=sender._meta.app_label,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            old_data=getattr(instance, "_old_data", None),
            new_data=model_to_dict_simple(instance),
        )
    except Exception:
        logger.exception(
            "Error creating AuditLog | model=%s | pk=%s",
            sender.__name__,
            instance.pk,
        )


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    if sender in EXCLUDED_MODELS:
        return

    logger.warning(
        "DELETE | model=%s | pk=%s | user=%s | ip=%s",
        sender.__name__,
        instance.pk,
        get_current_user(),
        get_current_ip(),
    )

    try:
        AuditLog.objects.create(
            user=get_current_user(),
            ip_address=get_current_ip(),
            action="DELETE",
            app_label=sender._meta.app_label,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            old_data=model_to_dict_simple(instance),
            new_data=None,
        )
    except Exception:
        logger.exception(
            "Error creating DELETE AuditLog | model=%s | pk=%s",
            sender.__name__,
            instance.pk,
        )
