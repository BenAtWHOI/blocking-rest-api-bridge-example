from django.apps import AppConfig


class RestApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rest_api'

    def ready(self):
        # Initialize database and table
        from . import startup_task
        startup_task.init_db()