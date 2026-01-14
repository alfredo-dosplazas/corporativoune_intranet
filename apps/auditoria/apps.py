from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    name = 'apps.auditoria'

    def ready(self):
        import apps.auditoria.signals
