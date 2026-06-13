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
