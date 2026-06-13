from django import forms
from django.utils import timezone

from equipment.models import Bow
from sessions.models import Session


class SessionForm(forms.ModelForm):
    """Add/edit a training session — objective fields.

    session_type is excluded and set programmatically to FREE_PRACTICE by the view.
    """

    class Meta:
        model = Session
        fields = [
            "name", "date", "bow", "location", "distance_m",
            "total_arrows", "scoring_arrows", "target_face", "total_score",
            "notes", "next_focus",
        ]
        widgets = {
            "date":          forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "distance_m":    forms.NumberInput(attrs={"list": "distance-suggestions", "min": "1"}),
            "total_arrows":  forms.NumberInput(attrs={"min": "1"}),
            "scoring_arrows": forms.NumberInput(attrs={"min": "1"}),
            "total_score":   forms.NumberInput(attrs={"min": "0"}),
            "notes":         forms.Textarea(attrs={"rows": 3}),
            "next_focus":    forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "distance_m":    "Distance (m)",
            "total_arrows":  "Total arrows",
            "scoring_arrows": "Scoring arrows",
            "target_face":   "Target face",
            "total_score":   "Total score",
            "next_focus":    "Focus for next session",
        }
        help_texts = {
            "total_arrows":  "Total number of arrows shot in this session (warmup + scored + cooldown + any blank-bale).",
            "scoring_arrows": "How many of those arrows were shot at a target face for scoring? Leave blank for blank-bale sessions.",
            "total_score":   "Points scored from the scoring arrows.",
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["bow"].queryset = Bow.objects.order_by("name")
        self.fields["bow"].required = False
        self.fields["bow"].empty_label = "— Leave empty —"
        self.fields["target_face"].required = False
        self.fields["target_face"].choices = [("", "— None —")] + list(Session.TargetFace.choices)
        today = timezone.localdate()
        self.fields["date"].widget.attrs["max"] = today.isoformat()
        if not self.instance.pk:
            self.fields["date"].initial = today

    def clean_date(self) -> object:
        date = self.cleaned_data.get("date")
        if date and date > timezone.localdate():
            raise forms.ValidationError("Session date cannot be in the future.")
        return date
