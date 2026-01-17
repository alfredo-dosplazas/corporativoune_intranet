from django.apps import AppConfig


class PapeleriaConfig(AppConfig):
    name = 'apps.papeleria'

    def ready(self):
        import apps.papeleria.signals