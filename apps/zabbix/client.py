from django.conf import settings
from zabbix_utils import ZabbixAPI
import time


class ZabbixClient:
    def get_api(self):
        api = ZabbixAPI(url=settings.ZABBIX_API_URL)
        # Soportar autenticación por Token o Usuario/Password
        if hasattr(settings, 'ZABBIX_TOKEN') and settings.ZABBIX_TOKEN:
            api.login(token=settings.ZABBIX_TOKEN)
        else:
            api.login(user=settings.ZABBIX_USER, password=settings.ZABBIX_PASSWORD)
        return api

    def get_hosts_criticos(self):
        """Obtiene los hosts que pertenecen a un grupo 'Criticos' o similar."""
        api = self.get_api()
        return api.host.get(
            output=["hostid", "name", "status"],
            selectInterfaces=["ip"],
            filter={"status": 0}  # 0 = Monitoreado activo
        )

    def get_problemas_actuales(self):
        """
        Retorna los problemas activos en Zabbix para calcular disponibilidad 
        y tiempo de inactividad (downtime).
        """
        api = self.get_api()
        # Traemos eventos de problemas activos (value=1)
        problems = api.problem.get(
            output=["eventid", "objectid", "severity", "name", "clock", "r_eventid"],
            severities=[3, 4, 5],  # Average, High, Disaster
            sortfield=["clock"],
            sortorder="DESC"
        )

        ahora = int(time.time())
        resultado = []

        for p in problems:
            tiempo_inicio = int(p['clock'])
            duracion_segundos = ahora - tiempo_inicio

            # Formatear el tiempo de caída de forma amigable
            horas = duracion_segundos // 3600
            minutos = (duracion_segundos % 3600) // 60
            tiempo_transcurrido_str = f"{horas}h {minutos}m" if horas > 0 else f"{minutos} mins"

            resultado.append({
                "evento_id": p['eventid'],
                "nombre_alerta": p['name'],
                "severidad": p['severity'],
                "tiempo_inicio": tiempo_inicio,
                "tiempo_caido": tiempo_transcurrido_str,
                "duracion_segundos": duracion_segundos
            })

        return resultado