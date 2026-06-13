import datetime

import pytest
from django.utils import timezone

from sessions.forms import SessionForm


def _form(date: datetime.date) -> SessionForm:
    return SessionForm(
        {
            "session-name": "Test Session",
            "session-date": date.isoformat(),
            "session-location": "indoor",
        },
        prefix="session",
    )


@pytest.mark.django_db
class TestSessionFormDateValidation:
    def test_today_is_valid(self):
        form = _form(timezone.localdate())
        assert form.is_valid()

    def test_yesterday_is_valid(self):
        form = _form(timezone.localdate() - datetime.timedelta(days=1))
        assert form.is_valid()

    def test_tomorrow_is_invalid(self):
        form = _form(timezone.localdate() + datetime.timedelta(days=1))
        assert not form.is_valid()
        assert "date" in form.errors

    def test_far_future_is_invalid(self):
        form = _form(timezone.localdate() + datetime.timedelta(days=365 * 5))
        assert not form.is_valid()
        assert "date" in form.errors


@pytest.mark.django_db
class TestSessionFormNextFocus:
    def test_blank_next_focus_is_valid(self):
        form = SessionForm(
            {
                "session-name": "Test Session",
                "session-date": timezone.localdate().isoformat(),
                "session-location": "indoor",
                "session-next_focus": "",
            },
            prefix="session",
        )
        assert form.is_valid()

    def test_text_next_focus_is_valid(self):
        form = SessionForm(
            {
                "session-name": "Test Session",
                "session-date": timezone.localdate().isoformat(),
                "session-location": "indoor",
                "session-next_focus": "Work on follow-through",
            },
            prefix="session",
        )
        assert form.is_valid()
        assert form.cleaned_data["next_focus"] == "Work on follow-through"


@pytest.mark.django_db
class TestSessionFormScoringFields:
    def _base(self) -> dict:
        return {
            "session-name": "Test Session",
            "session-date": timezone.localdate().isoformat(),
            "session-location": "indoor",
        }

    def test_complete_scored_session_is_valid(self):
        data = {
            **self._base(),
            "session-total_arrows": "90",
            "session-scoring_arrows": "72",
            "session-target_face": "122cm",
            "session-total_score": "657",
        }
        form = SessionForm(data, prefix="session")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["total_arrows"] == 90
        assert form.cleaned_data["scoring_arrows"] == 72
        assert form.cleaned_data["target_face"] == "122cm"
        assert form.cleaned_data["total_score"] == 657

    def test_blank_bale_session_only_total_arrows_is_valid(self):
        data = {**self._base(), "session-total_arrows": "80"}
        form = SessionForm(data, prefix="session")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["total_arrows"] == 80
        assert form.cleaned_data["scoring_arrows"] is None
        assert form.cleaned_data["target_face"] in ("", None)
        assert form.cleaned_data["total_score"] is None

    def test_all_scoring_fields_blank_is_valid(self):
        form = SessionForm(self._base(), prefix="session")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["total_arrows"] is None

    def test_invalid_target_face_choice_is_rejected(self):
        data = {**self._base(), "session-target_face": "garbage_face"}
        form = SessionForm(data, prefix="session")
        assert not form.is_valid()
        assert "target_face" in form.errors


@pytest.mark.django_db
class TestSessionFormSubjectiveFields:
    def _base(self) -> dict:
        return {
            "session-name": "Test Session",
            "session-date": timezone.localdate().isoformat(),
            "session-location": "indoor",
        }

    def test_all_subjective_fields_blank_is_valid(self):
        """Form accepts a session with no subjective data at all."""
        form = SessionForm(self._base(), prefix="session")
        assert form.is_valid(), form.errors

    def test_all_subjective_fields_filled_is_valid(self):
        """Form accepts a session with every subjective field populated."""
        data = {
            **self._base(),
            "session-time_of_day": "morning",
            "session-weather": "overcast",
            "session-temperature_celsius": "-5",
            "session-wind_force": "2",
            "session-wind_direction": "from_left",
            "session-nutrition": "4",
            "session-sleep_hours": "7.5",
            "session-sleep_notes": "Good quality",
            "session-stress": "2",
            "session-fatigue": "3",
            "session-physical_sensations": "Slight shoulder tightness",
        }
        form = SessionForm(data, prefix="session")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["time_of_day"] == "morning"
        assert form.cleaned_data["temperature_celsius"] == -5
        assert form.cleaned_data["wind_force"] == 2
        assert form.cleaned_data["nutrition"] == 4
        assert float(form.cleaned_data["sleep_hours"]) == 7.5
        assert form.cleaned_data["stress"] == 2
        assert form.cleaned_data["fatigue"] == 3

    def test_integer_scale_dropdowns_show_labels_not_numbers(self):
        """The rendered HTML for integer-choice dropdowns shows labels only.

        Users must never see raw integers as the visible option text.
        """
        form = SessionForm(prefix="session")
        html = form.as_p()
        # Labels that must appear for each integer-scale field
        for label in ("Calm", "Light", "Medium", "Strong", "Very strong",  # wind_force
                      "Very poor", "Poor", "OK", "Good", "Very good",       # nutrition
                      "Very low", "Low", "High", "Very high"):               # stress / fatigue
            assert label in html, f"Expected label '{label}' not found in rendered form"
        # The integer values 1–5 must NOT appear as bare option values visible to the user.
        # In Django's rendered select widgets the value goes in the value="" attribute,
        # not as visible text — but we verify the option text contains no raw digits.
        import re
        # Match option tags and check their visible text is never a lone digit
        option_texts = re.findall(r'<option[^>]*>([^<]+)</option>', html)
        for text in option_texts:
            stripped = text.strip()
            assert not re.fullmatch(r'\d+', stripped), (
                f"Option text '{stripped}' looks like a raw integer — labels expected"
            )

    def test_invalid_wind_force_value_is_rejected(self):
        data = {**self._base(), "session-wind_force": "6"}
        form = SessionForm(data, prefix="session")
        assert not form.is_valid()
        assert "wind_force" in form.errors

    def test_invalid_weather_choice_is_rejected(self):
        data = {**self._base(), "session-weather": "tornado"}
        form = SessionForm(data, prefix="session")
        assert not form.is_valid()
        assert "weather" in form.errors

    def test_sleep_hours_negative_is_rejected(self):
        data = {**self._base(), "session-sleep_hours": "-1"}
        form = SessionForm(data, prefix="session")
        assert not form.is_valid()
        assert "sleep_hours" in form.errors

    def test_sleep_hours_above_24_is_rejected(self):
        data = {**self._base(), "session-sleep_hours": "25"}
        form = SessionForm(data, prefix="session")
        assert not form.is_valid()
        assert "sleep_hours" in form.errors
