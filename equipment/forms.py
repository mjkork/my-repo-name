from django import forms

from equipment.models import Bow


class BowForm(forms.ModelForm):
    """Form for creating a new Bow (base fields only)."""

    class Meta:
        model = Bow
        fields = ["name", "type", "draw_weight_lbs", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
