from apps.core.utils.network import get_client_ip
from .models import UserAccessLog


class UserAccessLogMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            UserAccessLog.objects.create(
                user=request.user,
                ip_address=get_client_ip(request),
                path=request.path,
                method=request.method,
                user_agent=request.META.get("HTTP_USER_AGENT", "")
            )
        else:
            UserAccessLog.objects.create(
                user=None,
                ip_address=get_client_ip(request),
                path=request.path,
                method=request.method,
                user_agent=request.META.get("HTTP_USER_AGENT", "")
            )

        return response
