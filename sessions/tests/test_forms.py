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
