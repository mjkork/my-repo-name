from django import forms

from preferences.models import UserPreferences

SESSIONS_PER_PAGE_CHOICES = [(i, str(i)) for i in range(5, 11)]


class UserPreferencesForm(forms.ModelForm):
    sessions_per_page = forms.TypedChoiceField(
        choices=SESSIONS_PER_PAGE_CHOICES,
        coerce=int,
        label="The amount of sessions shown per page",
    )

    class Meta:
        model = UserPreferences
        fields = ["sessions_per_page"]
