from django.db import models
from django.utils import timezone

from equipment.models import Bow


class Session(models.Model):
    """A single training session at the range."""

    class Location(models.TextChoices):
        INDOOR = "indoor", "Indoor"
        OUTDOOR = "outdoor", "Outdoor"

    class SessionType(models.TextChoices):
        FREE_PRACTICE = "free_practice", "Free practice"

    name = models.CharField(max_length=100)
    date = models.DateField(default=timezone.localdate)
    bow = models.ForeignKey(
        Bow,
        on_delete=models.PROTECT,  # prevents deleting a bow that has sessions referencing it
        related_name="sessions",
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=20, choices=Location.choices)
    session_type = models.CharField(
        max_length=30,
        choices=SessionType.choices,
        default=SessionType.FREE_PRACTICE,
    )
    distance_m = models.PositiveSmallIntegerField(null=True, blank=True)
    arrow_count = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    next_focus = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.name} — {self.date}"
