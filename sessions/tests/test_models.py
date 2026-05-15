import pytest

from sessions.models import Session
from sessions.tests.factories import SessionFactory


@pytest.mark.django_db
class TestSessionModel:
    def test_session_can_be_saved_with_bow_none(self):
        session = SessionFactory(bow=None)
        assert session.pk is not None
        assert session.bow is None

    def test_session_str(self):
        session = SessionFactory(name="Morning practice", date="2025-05-01")
        assert str(session) == "Morning practice — 2025-05-01"

    def test_session_default_type_is_free_practice(self):
        session = SessionFactory()
        assert session.session_type == Session.SessionType.FREE_PRACTICE
