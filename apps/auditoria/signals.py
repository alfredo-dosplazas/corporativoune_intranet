from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from apps.core.utils.network import get_client_ip
from .models import UserAccessLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserAccessLog.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        path="LOGIN",
        method="AUTH",
        user_agent=request.META.get("HTTP_USER_AGENT", "")
    )
