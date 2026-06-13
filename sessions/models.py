from django.core.validators import MaxValueValidator, MinValueValidator
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

    class TimeOfDay(models.TextChoices):
        MORNING = "morning", "Morning"
        DAY = "day", "Day"
        AFTERNOON = "afternoon", "Afternoon"
        EVENING = "evening", "Evening"

    class Weather(models.TextChoices):
        SUNNY = "sunny", "Sunny"
        PARTLY_CLOUDY = "partly_cloudy", "Partly cloudy"
        OVERCAST = "overcast", "Overcast"
        RAINY = "rainy", "Rainy"

    class WindForce(models.IntegerChoices):
        CALM = 1, "Calm"
        LIGHT = 2, "Light"
        MEDIUM = 3, "Medium"
        STRONG = 4, "Strong"
        VERY_STRONG = 5, "Very strong"

    class WindDirection(models.TextChoices):
        FROM_LEFT = "from_left", "From left"
        FROM_RIGHT = "from_right", "From right"
        FROM_FRONT = "from_front", "From front"
        FROM_BACK = "from_back", "From back"
        FROM_FRONT_LEFT = "from_front_left", "From front-left"
        FROM_FRONT_RIGHT = "from_front_right", "From front-right"
        FROM_BACK_LEFT = "from_back_left", "From back-left"
        FROM_BACK_RIGHT = "from_back_right", "From back-right"

    class Nutrition(models.IntegerChoices):
        VERY_POOR = 1, "Very poor"
        POOR = 2, "Poor"
        OK = 3, "OK"
        GOOD = 4, "Good"
        VERY_GOOD = 5, "Very good"

    class Stress(models.IntegerChoices):
        VERY_LOW = 1, "Very low"
        LOW = 2, "Low"
        MEDIUM = 3, "Medium"
        HIGH = 4, "High"
        VERY_HIGH = 5, "Very high"

    class Fatigue(models.IntegerChoices):
        VERY_LOW = 1, "Very low"
        LOW = 2, "Low"
        MEDIUM = 3, "Medium"
        HIGH = 4, "High"
        VERY_HIGH = 5, "Very high"

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
    # Environmental conditions
    time_of_day = models.CharField(
        max_length=20, choices=TimeOfDay.choices, null=True, blank=True
    )
    weather = models.CharField(
        max_length=20, choices=Weather.choices, null=True, blank=True
    )
    temperature_celsius = models.SmallIntegerField(null=True, blank=True)
    wind_force = models.PositiveSmallIntegerField(
        choices=WindForce.choices, null=True, blank=True
    )
    wind_direction = models.CharField(
        max_length=20, choices=WindDirection.choices, null=True, blank=True
    )
    # Personal state (before session)
    nutrition = models.PositiveSmallIntegerField(
        choices=Nutrition.choices, null=True, blank=True
    )
    sleep_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    sleep_notes = models.TextField(blank=True)
    stress = models.PositiveSmallIntegerField(
        choices=Stress.choices, null=True, blank=True
    )
    # Session experience (end of session)
    fatigue = models.PositiveSmallIntegerField(
        choices=Fatigue.choices, null=True, blank=True
    )
    physical_sensations = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    next_focus = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.name} — {self.date}"
