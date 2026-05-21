from django.apps import AppConfig
import os

class UsuariosConfig(AppConfig):
    name = "usuarios"

    def ready(self):
        import sys
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            if os.environ.get('DISABLE_SCHEDULER') != 'true':
                from . import scheduler
                scheduler.start()