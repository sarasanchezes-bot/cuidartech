from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    name = "usuarios"

    def ready(self):
        import sys
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            from . import scheduler
            scheduler.start()