from apps.core.utils.network import ping

ACCESS_POINTS = [
    {"nombre": "AP Dirección (AP325)", "ip": "172.17.0.245"},
    {"nombre": "AP Ventas (AP225W)", "ip": "172.17.0.246"},
    {"nombre": "AP BBH (AP225W)", "ip": "172.17.0.247"},
    {"nombre": "AP Sala BBH (AP225W)", "ip": "172.17.0.248"},
    {"nombre": "AP Sistemas (AP225W)", "ip": "172.17.0.249"},
]


def obtener_estado_access_points():
    aps = []

    for ap in ACCESS_POINTS:
        result = ping(ap["ip"])

        aps.append({
            "nombre": ap["nombre"],
            "ip": ap["ip"],
            "estado": "online" if result["online"] else "offline",
            "latencia": result["latencia"]
        })

    return aps
