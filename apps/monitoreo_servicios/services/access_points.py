from apps.core.utils.network import ping

ACCESS_POINTS = [
    {"nombre": "AP Ventas (AP330)", "ip": "172.17.0.1"},
    {"nombre": "AP Sistemas (AP330)", "ip": "172.17.0.4"},
    {"nombre": "AP BBH (AP330)", "ip": "172.17.0.5"},
    {"nombre": "AP Proyectos (AP330)", "ip": "172.17.0.6"},
    {"nombre": "AP Dirección (AP330)", "ip": "172.17.0.7"},
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
