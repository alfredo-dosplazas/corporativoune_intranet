import logging
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)


class SlackClient:

    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)

    def get_user_list(self):
        return self.client.users_list()

    def get_slack_id_by_email(self, email: str):
        try:
            response = self.client.users_list()
            for user in response["members"]:
                if user.get("profile", {}).get("email") == email:
                    return user["id"]
        except SlackApiError as e:
            logger.error("Error obteniendo usuarios de Slack: %s", e.response["error"])
        return None

    def send_message(self, target_id: str, message: str) -> bool:
        """
        Envía mensaje a:
        - Usuario (Uxxxx)
        - Canal público (Cxxxx)
        - Canal privado (Gxxxx)
        """

        try:
            # Si es usuario, abrimos DM
            if target_id.startswith("U"):
                response = self.client.conversations_open(users=target_id)
                channel_id = response["channel"]["id"]
            else:
                # Canal público o privado
                channel_id = target_id

            self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                mrkdwn=True,
            )

            return True

        except SlackApiError as e:
            error_code = e.response.get("error")

            if error_code == "not_in_channel":
                logger.warning(
                    "El bot no está en el canal %s. Error: %s",
                    target_id,
                    error_code
                )
            else:
                logger.error(
                    "Error enviando mensaje a %s: %s",
                    target_id,
                    error_code
                )

            return False