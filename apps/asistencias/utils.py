from datetime import time


def minutos_a_hora(minutos):
    if minutos is None or minutos < 0:
        return None

    minutos = int(minutos)
    horas = minutos // 60
    mins = minutos % 60
    print(horas, mins)
    return time(hour=horas, minute=mins)