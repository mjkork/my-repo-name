from django import forms

from equipment.models import Bow, OlympicBowSetup


class BowForm(forms.ModelForm):
    """Base bow fields — name, type, draw weight, notes."""

    class Meta:
        model = Bow
        fields = ["name", "type", "draw_weight_lbs", "notes"]
        widgets = {
            "draw_weight_lbs": forms.NumberInput(attrs={"step": "0.5"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class OlympicBowSetupForm(forms.ModelForm):
    """Olympic Recurve component fields — all optional free-text."""

    class Meta:
        model = OlympicBowSetup
        fields = [
            "riser", "limbs", "arrow_rest", "sight",
            "main_stabilizer", "extender", "side_stabilizers",
            "v_bar", "clicker", "button",
        ]
        labels = {
            "arrow_rest":       "Arrow rest",
            "main_stabilizer":  "Main stabilizer",
            "side_stabilizers": "Side stabilizers",
            "v_bar":            "V-bar",
            "button":           "Button (plunger)",
        }
