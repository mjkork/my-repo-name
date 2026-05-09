from django.apps import AppConfig


class SessionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sessions"
    label = "practice_sessions"  # avoids clash with django.contrib.sessions label
