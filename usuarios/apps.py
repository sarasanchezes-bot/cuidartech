from django.apps import AppConfig
import os

class UsuariosConfig(AppConfig):
    name = "usuarios"

    def ready(self):
        import sys
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                from . import scheduler
                scheduler.start()