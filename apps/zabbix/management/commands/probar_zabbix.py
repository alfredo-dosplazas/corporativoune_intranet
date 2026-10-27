from django.core.management.base import BaseCommand
from apps.zabbix.client import ZabbixClient


class Command(BaseCommand):
    help = "Prueba la conexión con Zabbix y lista el estado y problemas de los equipos."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Conectando con Zabbix..."))

        try:
            client = ZabbixClient()

            # 1. Probar hosts
            hosts = client.get_hosts_criticos()
            self.stdout.write(self.style.SUCCESS(f"✅ Conexión exitosa. Hosts activos encontrados: {len(hosts)}"))
            for h in hosts[:5]:  # Mostrar los primeros 5
                self.stdout.write(f" - Host: {h['name']} (ID: {h['hostid']})")

            # 2. Probar problemas y tiempos de caída
            problemas = client.get_problemas_actuales()
            self.stdout.write(self.style.WARNING(f"\n🚨 Problemas críticos activos actuales: {len(problemas)}"))

            for p in problemas:
                self.stdout.write(
                    f"   [!] {p['nombre_alerta']} | Tiempo caído: {p['tiempo_caido']}"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al conectar con Zabbix: {e}"))
