from django.apps import AppConfig


class HelloWorldConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hello_world'

    def ready(self):
        import hello_world.signals
