from django.http import HttpResponseForbidden
from apps.core.utils.network import get_client_ip, ip_in_allowed_range


def internal_network_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        ip = get_client_ip(request)

        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view
