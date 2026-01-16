import base64

from django.conf import settings
import requests
from requests.auth import HTTPDigestAuth

from apps.monitoreo_servicios.dahua_nvr_client import DahuaNVRClient

CCTV_USER = settings.CCTV_USER
CCTV_PASSWORD = settings.CCTV_PASSWORD

CCTV = {
    'NVR PRINCIPAL': {
        'ip': '172.17.3.202',
        'camaras': [
            {
                'nombre': 'Recepción',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 3,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=3'
            },
            {
                'nombre': 'Proyectos',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 1,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=1'
            },
            {
                'nombre': 'Contabilidad FP',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 5,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=5'
            },
            {
                'nombre': 'Site',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 2,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=2'
            },
            {
                'nombre': 'Sala De Juntas',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 4,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=4'
            },
            {
                'nombre': 'Tesorería',
                'ip': '172.17.3.202',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 6,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=6'
            },
        ],
    },
    'NVR VENTAS': {
        'ip': '172.17.3.203',
        'camaras': [
            {
                'nombre': 'Sala De Juntas Ventas',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 1,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=1'
            },
            {
                'nombre': 'Oficina RH',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 2,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=2'
            },
            {
                'nombre': 'Entrada Ampliación',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 3,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=3'
            },
            {
                'nombre': 'Cocineta Amplicación',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 4,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=4'
            },
            {
                'nombre': 'Entrada Estacionamiento',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 6,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=6'
            },
            {
                'nombre': 'Estacionamiento Oeste',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 5,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=5'
            },
            {
                'nombre': 'Estacionamiento Este',
                'ip': '172.17.3.203',
                'port': '',
                'usuario': CCTV_USER,
                'password': CCTV_PASSWORD,
                'channel': 7,
                'snapshot_url': f'http://172.17.3.202/cgi-bin/snapshot.cgi?channel=7'
            },
        ]
    }
}


def obtener_snapshot(ip, usuario, password, channel, timeout=5):
    url = f"http://{ip}/cgi-bin/snapshot.cgi"

    try:
        r = requests.get(
            url,
            params={"channel": channel},
            auth=HTTPDigestAuth(usuario, password),
            timeout=timeout
        )

        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/"):
            return {
                "ok": True,
                "base64": base64.b64encode(r.content).decode()
            }

    except requests.RequestException:
        pass

    return {"ok": False, "base64": None}


def obtener_estado_cctv():
    reporte = []

    for nvr, data in CCTV.items():
        cams = []

        ip = data['ip']
        camaras = data['camaras']

        nvr_client = DahuaNVRClient(
            host=ip,
            username=CCTV_USER,
            password=CCTV_PASSWORD,
        )

        grabando_desde, grabando_hasta = nvr_client.find_recording_range()

        for cam in camaras:
            snapshot = obtener_snapshot(
                cam["ip"],
                cam["usuario"],
                cam["password"],
                cam["channel"]
            )

            cams.append({
                "nombre": cam["nombre"],
                "ip": cam["ip"],
                "canal": cam["channel"],
                "estado": "online" if snapshot["ok"] else "offline",
                "snapshot_base64": snapshot["base64"],
            })

        reporte.append({
            "nvr": nvr,
            "grabando_desde": grabando_desde,
            "grabando_hasta": grabando_hasta,
            "total": len(cams),
            "operativas": sum(1 for c in cams if c["estado"] == "online"),
            "sin_senal": sum(1 for c in cams if c["estado"] == "offline"),
            "camaras": cams,
        })

    return reporte
