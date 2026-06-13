from django import forms
from django.utils import timezone

from equipment.models import Bow
from sessions.models import Session


class SessionForm(forms.ModelForm):
    """Add/edit a training session.

    session_type is excluded and set programmatically to FREE_PRACTICE by the view.
    All subjective variable fields are optional and rendered as a flat list (Prompt 2A).
    Form sections and indoor/outdoor conditional display come in Prompt 2B.
    """

    class Meta:
        model = Session
        fields = [
            # Session basics
            "name", "date", "bow", "location",
            # Shooting details
            "distance_m", "total_arrows", "scoring_arrows", "target_face", "total_score",
            # Environmental conditions
            "time_of_day", "weather", "temperature_celsius", "wind_force", "wind_direction",
            # Personal state
            "nutrition", "sleep_hours", "sleep_notes", "stress",
            # Session experience
            "fatigue", "physical_sensations",
            # Reflection
            "notes", "next_focus",
        ]
        widgets = {
            "date":                forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "distance_m":          forms.NumberInput(attrs={"list": "distance-suggestions", "min": "1"}),
            "total_arrows":        forms.NumberInput(attrs={"min": "1"}),
            "scoring_arrows":      forms.NumberInput(attrs={"min": "1"}),
            "total_score":         forms.NumberInput(attrs={"min": "0"}),
            "temperature_celsius": forms.NumberInput(),
            "sleep_hours":         forms.NumberInput(attrs={"min": "0", "max": "24", "step": "0.5"}),
            "sleep_notes":         forms.Textarea(attrs={"rows": 2}),
            "physical_sensations": forms.Textarea(attrs={"rows": 2}),
            "notes":               forms.Textarea(attrs={"rows": 3}),
            "next_focus":          forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "distance_m":          "Distance (m)",
            "total_arrows":        "Total arrows",
            "scoring_arrows":      "Scoring arrows",
            "target_face":         "Target face",
            "total_score":         "Total score",
            "time_of_day":         "Time of day",
            "weather":             "Weather",
            "temperature_celsius": "Temperature (°C)",
            "wind_force":          "Wind force",
            "wind_direction":      "Wind direction",
            "nutrition":           "Nutrition before session",
            "sleep_hours":         "Hours of sleep last night",
            "sleep_notes":         "Sleep notes",
            "stress":              "Stress level during session",
            "fatigue":             "Fatigue at end of session",
            "physical_sensations": "Physical sensations",
            "next_focus":          "Focus for next session",
        }
        help_texts = {
            "total_arrows":        "Total number of arrows shot in this session (warmup + scored + cooldown + any blank-bale).",
            "scoring_arrows":      "How many of those arrows were shot at a target face for scoring? Leave blank for blank-bale sessions.",
            "total_score":         "Points scored from the scoring arrows.",
            "sleep_notes":         "Optional. Quality, restlessness, anything worth noting.",
            "physical_sensations": "Optional. Tightness, discomfort, anything notable from your body during the session.",
        }

    _BLANK_CHOICE = [("", "—")]

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["bow"].queryset = Bow.objects.order_by("name")
        self.fields["bow"].required = False
        self.fields["bow"].empty_label = "— Leave empty —"

        # All choice fields get a blank "—" option and are not required
        optional_choice_fields = [
            ("target_face", Session.TargetFace.choices),
            ("time_of_day", Session.TimeOfDay.choices),
            ("weather", Session.Weather.choices),
            ("wind_force", Session.WindForce.choices),
            ("wind_direction", Session.WindDirection.choices),
            ("nutrition", Session.Nutrition.choices),
            ("stress", Session.Stress.choices),
            ("fatigue", Session.Fatigue.choices),
        ]
        for field_name, choices in optional_choice_fields:
            self.fields[field_name].required = False
            self.fields[field_name].choices = self._BLANK_CHOICE + list(choices)

        today = timezone.localdate()
        self.fields["date"].widget.attrs["max"] = today.isoformat()
        if not self.instance.pk:
            self.fields["date"].initial = today

    def clean_date(self) -> object:
        date = self.cleaned_data.get("date")
        if date and date > timezone.localdate():
            raise forms.ValidationError("Session date cannot be in the future.")
        return date
