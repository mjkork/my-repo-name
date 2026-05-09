from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model — extend here rather than swapping later."""
