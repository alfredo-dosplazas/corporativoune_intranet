from datetime import datetime, timedelta

import requests
from requests.auth import HTTPDigestAuth

from apps.monitoreo_servicios.tasks.cctv import cleanup_nvr_factory


class DahuaNVRClient:
    def __init__(self, host, username, password, timeout=10):
        self.host = host
        self.base_url = f"http://{host}/cgi-bin"
        self.auth = HTTPDigestAuth(username, password)
        self.timeout = timeout

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(
            url,
            params=params,
            auth=self.auth,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.text

    def factory_create(self):
        text = self._get("mediaFileFind.cgi", {"action": "factory.create"})
        return text.strip().split("=")[1]

    def factory_close(self, factory_id):
        self._get(
            "mediaFileFind.cgi",
            {"action": "close", "object": factory_id}
        )

    def factory_destroy(self, factory_id):
        self._get(
            "mediaFileFind.cgi",
            {"action": "destroy", "object": factory_id}
        )

    def find_recording_range(self, weeks_back=24):
        factory_id = self.factory_create()

        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(weeks=weeks_back)

            params = {
                "action": "findFile",
                "object": factory_id,
                "condition.Channel": 1,
                "condition.StartTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "condition.EndTime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "condition.Types[0]": "dav",
                "condition.Dirs[0]": "/mnt/dvr/sda0",
            }

            result = self._get("mediaFileFind.cgi", params)

            if "OK" not in result.upper():
                return None, None

            oldest = None
            newest = None

            while True:
                data = self._get(
                    "mediaFileFind.cgi",
                    {
                        "action": "findNextFile",
                        "object": factory_id,
                        "count": 100,
                    },
                )

                lines = data.split("\r\n")

                found_line = next((l for l in lines if l.startswith("found=")), None)
                if not found_line or int(found_line.split("=")[1]) == 0:
                    break

                for line in lines:
                    if ".StartTime" in line:
                        value = line.split("=", 1)[1].strip()
                        t = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                        if not oldest or t < oldest:
                            oldest = t
                        if not newest or t > newest:
                            newest = t
            return oldest, newest


        finally:
            cleanup_nvr_factory.delay(
                self.host,
                self.auth.username,
                self.auth.password,
                factory_id,
            )
