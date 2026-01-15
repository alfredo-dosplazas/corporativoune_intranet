from django.conf import settings
from slack_sdk import WebClient


class SlackClient:
    SLACK_BOT_TOKEN = settings.SLACK_BOT_TOKEN

    client = WebClient(token=SLACK_BOT_TOKEN)

    def get_user_list(self):
        return self.client.users_list()

    def get_slack_id_por_email(self, users, email):
        for u in users["members"]:
            if u["profile"].get("email") == email:
                return u["id"]
        return None

    def send_bot_message_from_id(self, slack_id: str, message: str):
        response = self.client.conversations_open(users=slack_id)
        channel_id = response["channel"]["id"]

        self.client.chat_postMessage(channel=channel_id, text=message, mrkdwn=True)
