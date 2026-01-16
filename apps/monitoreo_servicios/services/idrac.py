import requests
import logging
from django.conf import settings
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("monitoreo_servicios.services.idrac")

IDRAC_IP = "172.17.2.101"
IDRAC_USER = settings.IDRAC_USER
IDRAC_PASSWORD = settings.IDRAC_PASSWORD


def obtener_estado_idrac():
    base = f"https://{IDRAC_IP}/redfish/v1"
    auth = HTTPBasicAuth(IDRAC_USER, IDRAC_PASSWORD)

    def get_json(path):
        if "/redfish/v1/" in path:
            path = path.replace("/redfish/v1", "")
        url = path if path.startswith("http") else f"{base}{path}"
        try:
            r = requests.get(url, auth=auth, verify=False, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error("iDRAC error %s → %s", url, e)
            return {}

    logger.info("Consultando estado iDRAC %s", IDRAC_IP)

    # =======================
    # SISTEMA
    # =======================
    sys_data = get_json("/Systems/System.Embedded.1")

    sistema = {
        "nombre": sys_data.get("Name"),
        "modelo": sys_data.get("Model"),
        "fabricante": sys_data.get("Manufacturer"),
        "estado": sys_data.get("Status", {}).get("State"),
        "salud": sys_data.get("Status", {}).get("Health"),
        "power_state": sys_data.get("PowerState"),
        "hostname": sys_data.get("HostName"),
        "memoria_gib": sys_data.get("MemorySummary", {}).get("TotalSystemMemoryGiB"),
        "cpu_modelo": sys_data.get("ProcessorSummary", {}).get("Model"),
        "cores": sys_data.get("ProcessorSummary", {}).get("CoreCount"),
        "hilos": sys_data.get("ProcessorSummary", {}).get("LogicalProcessorCount"),
        "salud_cpu": sys_data.get("ProcessorSummary", {}).get("Status", {}).get("Health"),
        "serial": sys_data.get("SerialNumber"),
        "bios": sys_data.get("BiosVersion"),
        "uuid": sys_data.get("UUID"),
    }

    # =======================
    # ROLLUPS OEM DELL
    # =======================
    oem = sys_data.get("Oem", {}).get("Dell", {}).get("DellSystem", {})
    rollups = {
        "cpu": oem.get("CPURollupStatus"),
        "memoria": oem.get("SysMemPrimaryStatus"),
        "almacenamiento": oem.get("StorageRollupStatus"),
        "ventiladores": oem.get("FanRollupStatus"),
        "fuentes": oem.get("PSRollupStatus"),
        "temperatura": oem.get("TempRollupStatus"),
    }

    # =======================
    # ALMACENAMIENTO
    # =======================
    storages_data = get_json("/Systems/System.Embedded.1/Storage")
    almacenamiento = []

    for member in storages_data.get("Members", []):
        st = get_json(member["@odata.id"])
        almacenamiento.append({
            "nombre": st.get("Name"),
            "modelo": (
                st.get("StorageControllers", [{}])[0].get("Model")
                if st.get("StorageControllers")
                else "N/A"
            ),
            "estado": st.get("Status", {}).get("State"),
            "salud": st.get("Status", {}).get("Health"),
        })

    logger.info("Reporte iDRAC generado correctamente")

    return {
        "ip": IDRAC_IP,
        "sistema": sistema,
        "rollups": rollups,
        "almacenamiento": almacenamiento,
    }
