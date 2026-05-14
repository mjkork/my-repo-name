from django import forms
from django.utils import timezone

from equipment.models import Bow
from sessions.models import Session


class SessionForm(forms.ModelForm):
    """Add/edit a training session — v1 objective fields only.

    session_type is excluded and set programmatically to FREE_PRACTICE by the view.
    """

    class Meta:
        model = Session
        fields = ["name", "date", "bow", "location", "distance_m", "arrow_count", "notes"]
        widgets = {
            "date":       forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "distance_m": forms.NumberInput(attrs={"list": "distance-suggestions", "min": "1"}),
            "arrow_count": forms.NumberInput(attrs={"min": "1"}),
            "notes":      forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "distance_m":  "Distance (m)",
            "arrow_count": "Total arrows",
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["bow"].queryset = Bow.objects.order_by("name")
        if not self.instance.pk:
            self.fields["date"].initial = timezone.localdate()
