from django.conf import settings
from django.db import models


class Bow(models.Model):
    """A user's bow. Variant-specific fields live in a dedicated Setup model."""

    class BowType(models.TextChoices):
        OLYMPIC_RECURVE = "olympic_recurve", "Olympic Recurve"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bows",
    )
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50, choices=BowType.choices)
    draw_weight_lbs = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"


class OlympicBowSetup(models.Model):
    """Type-specific component fields for an Olympic Recurve bow.

    All component fields are optional free-text — the user fills in whatever
    they have. This model is the migration point if components ever become
    first-class Equipment entities.
    """

    bow = models.OneToOneField(
        Bow,
        on_delete=models.CASCADE,
        related_name="olympic_setup",
        limit_choices_to={"type": Bow.BowType.OLYMPIC_RECURVE},
    )
    riser = models.CharField(max_length=200, blank=True)
    limbs = models.CharField(max_length=200, blank=True)
    arrow_rest = models.CharField(max_length=200, blank=True)
    sight = models.CharField(max_length=200, blank=True)
    main_stabilizer = models.CharField(max_length=200, blank=True)
    extender = models.CharField(max_length=200, blank=True)
    side_stabilizers = models.CharField(max_length=200, blank=True)
    v_bar = models.CharField(max_length=200, blank=True)
    clicker = models.CharField(max_length=200, blank=True)
    button = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"Setup for {self.bow}"
