from apps.core.utils.network import ping

ACCESS_POINTS = [
    {"nombre": "AP Dirección (AP330)", "ip": "172.17.0.2"},
    {"nombre": "AP BBH (AP330)", "ip": "172.17.0.4"},
    {"nombre": "AP Sistemas (AP330)", "ip": "172.17.0.5"},
    {"nombre": "AP Ventas (AP330)", "ip": "172.17.0.6"},
    {"nombre": "AP Proyectos (AP330)", "ip": "172.17.0.7"},
]

MAX_LATENCIA_PERMITIDA = 2000

def obtener_estado_access_points():
    aps = []

    for ap in ACCESS_POINTS:
        result = ping(ap["ip"])

        # Un AP está online SI el ping respondió Y la latencia está bajo el umbral
        latencia = result["latencia"]
        esta_online = result["online"] and (latencia is not None and latencia < MAX_LATENCIA_PERMITIDA)

        aps.append({
            "nombre": ap["nombre"],
            "ip": ap["ip"],
            "estado": "online" if esta_online else "offline",
            "latencia": latencia
        })

    return aps
