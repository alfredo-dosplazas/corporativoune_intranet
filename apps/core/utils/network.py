import ipaddress
import logging

import subprocess
import platform
import time

from apps.core.models import EmpresaIPRange, Empresa

logger = logging.getLogger("core.network")


def ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", ip]

    start = time.time()
    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    latency = int((time.time() - start) * 1000)

    return {
        "online": result.returncode == 0,
        "latencia": latency if result.returncode == 0 else None
    }


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # Tomamos la primera IP de la lista
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


ALLOWED_NETWORKS = [
    ipaddress.ip_network("172.17.2.254/32"), # DP-SERVER
    ipaddress.ip_network("172.17.4.0/24"),  # VLAN de Usuarios Ethernet
    ipaddress.ip_network("172.17.5.0/24"),  # VLAN de Usuarios SSID Dos_Plazas
    ipaddress.ip_network("172.17.6.0/24"),  # VLAN de Usuarios SSID Dos_Plazas_D
    ipaddress.ip_network("172.17.7.0/24"),  # VLAN de Usuarios SSID Dos_Plazas_T
    ipaddress.ip_network("200.92.196.66/32"),  # IP Pública de FP
    ipaddress.ip_network("127.0.0.1/32"),
    ipaddress.ip_network("::1/128"),
]


def ip_in_allowed_range(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in ALLOWED_NETWORKS)
    except ValueError:
        return False


def get_empresa_from_ip(ip):
    if not ip:
        return None

    ip_obj = ipaddress.ip_address(ip)

    for ip_range in EmpresaIPRange.objects.filter(activa=True).select_related("empresa"):
        if ip_obj in ipaddress.ip_network(ip_range.cidr):
            return ip_range.empresa

    return None


def get_empresas_from_ip(ip: str):
    import ipaddress
    ip_addr = ipaddress.ip_address(ip)
    empresas = []

    for empresa in Empresa.objects.all():
        for net in empresa.allowed_networks.all():  # supongamos que cada empresa tiene un modelo relacionado de redes
            if ip_addr in ipaddress.ip_network(net.cidr):
                empresas.append(empresa)
                break
    return empresas
