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

    class TargetFace(models.TextChoices):
        CM_40 = "40cm", "40 cm standard"
        CM_40_3SPOT = "40cm 3-spot vertical", "40 cm 3-spot vertical"
        CM_60 = "60cm", "60 cm standard"
        CM_60_3SPOT = "60cm 3-spot", "60 cm 3-spot"
        CM_80 = "80cm", "80 cm"
        CM_122 = "122cm", "122 cm"

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
    total_arrows = models.PositiveIntegerField(null=True, blank=True)
    scoring_arrows = models.PositiveIntegerField(null=True, blank=True)
    target_face = models.CharField(
        max_length=40, choices=TargetFace.choices, null=True, blank=True
    )
    total_score = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    next_focus = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.name} — {self.date}"
