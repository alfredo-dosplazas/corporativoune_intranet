from django.apps import AppConfig


class RegalosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.regalos'

    def ready(self):
        import apps.regalos.signals  # noqa: F401 — registra los signals
