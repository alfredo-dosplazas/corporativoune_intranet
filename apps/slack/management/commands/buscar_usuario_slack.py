from django.core.management import BaseCommand

from apps.directorio.models import Contacto
from apps.slack.client import SlackClient


class Command(BaseCommand):
    help = 'Buscar usuario por ID'

    def handle(self, *args, **options):
        slack_client = SlackClient()
        user_list = slack_client.get_user_list()

        print(user_list)
