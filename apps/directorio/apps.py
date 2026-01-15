from django.apps import AppConfig


class DirectorioConfig(AppConfig):
    name = 'apps.directorio'

    def ready(self):
        import apps.directorio.signals
