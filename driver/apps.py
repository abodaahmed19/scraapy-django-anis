# from django.apps import AppConfig


# class DriverConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "driver"
    
#     def ready(self):
#         import driver.signals


from django.apps import AppConfig

class DriverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'driver'

    def ready(self):
        import driver.signals  # 👈 هذا هو المهم