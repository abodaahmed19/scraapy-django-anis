from django.apps import AppConfig


class BmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bms"

    def ready(self):
        import bms.signals
