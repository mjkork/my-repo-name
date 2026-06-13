import pytest
from django.core.exceptions import ValidationError

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

    def test_next_focus_defaults_to_empty_string(self):
        session = SessionFactory()
        assert session.next_focus == ""

    def test_next_focus_can_store_text(self):
        session = SessionFactory(next_focus="Work on follow-through")
        assert session.next_focus == "Work on follow-through"


@pytest.mark.django_db
class TestScoringFields:
    def test_all_scoring_fields_can_be_saved(self):
        session = SessionFactory(
            total_arrows=90,
            scoring_arrows=72,
            target_face=Session.TargetFace.CM_122,
            total_score=657,
        )
        session.refresh_from_db()
        assert session.total_arrows == 90
        assert session.scoring_arrows == 72
        assert session.target_face == "122cm"
        assert session.total_score == 657

    def test_all_scoring_fields_can_be_null(self):
        session = SessionFactory(
            total_arrows=None,
            scoring_arrows=None,
            target_face=None,
            total_score=None,
        )
        session.refresh_from_db()
        assert session.total_arrows is None
        assert session.scoring_arrows is None
        assert session.target_face is None
        assert session.total_score is None

    def test_target_face_rejects_invalid_choice(self):
        session = SessionFactory(target_face="garbage")
        with pytest.raises(ValidationError):
            session.full_clean()
