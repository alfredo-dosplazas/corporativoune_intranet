from django.core.management import BaseCommand

from apps.directorio.models import Contacto
from apps.slack.client import SlackClient


class Command(BaseCommand):
    help = 'Cargar ids de Slack para los contactos del corporativo'

    def handle(self, *args, **options):
        contactos = Contacto.objects.filter(
            email_slack__isnull=False,
            slack_id__isnull=True,
        )

        slack_client = SlackClient()
        user_list = slack_client.get_user_list()

        user_map = {}
        for user in user_list.get('members', []):
            profile = user.get('profile', {})
            email = profile.get('email')

            if email:
                user_map[email.lower()] = user.get('id')

        actualizados = 0

        for contacto in contactos:
            slack_id = user_map.get(contacto.email_slack.lower())

            if slack_id:
                contacto.slack_id = slack_id
                contacto.save(update_fields=['slack_id'])
                actualizados += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'{contacto.email_slack} → {slack_id}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'OK - {actualizados} contactos actualizados')
        )
