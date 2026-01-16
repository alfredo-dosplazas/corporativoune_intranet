from celery import shared_task
import requests
from requests.auth import HTTPDigestAuth
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def cleanup_nvr_factory(self, host, username, password, factory_id):
    base_url = f"http://{host}/cgi-bin"
    auth = HTTPDigestAuth(username, password)

    try:
        # CLOSE
        requests.get(
            f"{base_url}/mediaFileFind.cgi",
            params={"action": "close", "object": factory_id},
            auth=auth,
            timeout=5,
        )

        # DESTROY
        requests.get(
            f"{base_url}/mediaFileFind.cgi",
            params={"action": "destroy", "object": factory_id},
            auth=auth,
            timeout=5,
        )

        logger.info(
            "NVR factory cleanup OK | host=%s | factory_id=%s",
            host,
            factory_id,
        )

    except Exception as exc:
        logger.warning(
            "NVR factory cleanup FAILED | host=%s | factory_id=%s | %s",
            host,
            factory_id,
            exc,
        )
        raise