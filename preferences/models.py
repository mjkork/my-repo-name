from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserPreferences(models.Model):
    """Singleton that holds all user-configurable preferences.

    Access via UserPreferences.load() — never instantiate directly.
    Adding a new preference: add a field here with a sensible default,
    generate a migration, and expose it in the form/view as needed.
    Future candidates: bows_per_page, default_location, theme.
    """

    sessions_per_page = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(5), MaxValueValidator(10)],
    )

    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"

    def __str__(self) -> str:
        return "User Preferences"

    @classmethod
    def load(cls) -> "UserPreferences":
        """Return the singleton row, creating it with defaults if absent."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args: object, **kwargs: object) -> None:
        self.pk = 1
        super().save(*args, **kwargs)
