import ipaddress

import subprocess
import platform
import time


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
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


ALLOWED_NETWORKS = [
    ipaddress.ip_network("172.17.0.0/16"),
    ipaddress.ip_network("127.0.0.1/32"),
    ipaddress.ip_network("::1/128"),
]


def ip_in_allowed_range(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in ALLOWED_NETWORKS)
    except ValueError:
        return False
