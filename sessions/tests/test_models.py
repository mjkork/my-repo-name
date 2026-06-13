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


@pytest.mark.django_db
class TestSubjectiveVariableFields:
    def test_all_subjective_fields_can_be_null_or_blank(self):
        """Existing sessions without subjective data are valid."""
        session = SessionFactory(
            time_of_day=None,
            weather=None,
            temperature_celsius=None,
            wind_force=None,
            wind_direction=None,
            nutrition=None,
            sleep_hours=None,
            sleep_notes="",
            stress=None,
            fatigue=None,
            physical_sensations="",
        )
        session.full_clean()
        session.refresh_from_db()
        assert session.time_of_day is None
        assert session.weather is None
        assert session.temperature_celsius is None
        assert session.wind_force is None
        assert session.wind_direction is None
        assert session.nutrition is None
        assert session.sleep_hours is None
        assert session.sleep_notes == ""
        assert session.stress is None
        assert session.fatigue is None
        assert session.physical_sensations == ""

    def test_all_subjective_fields_can_be_populated(self):
        """Round-trip: every subjective field saves and loads correctly."""
        session = SessionFactory(
            time_of_day=Session.TimeOfDay.MORNING,
            weather=Session.Weather.OVERCAST,
            temperature_celsius=-5,
            wind_force=Session.WindForce.LIGHT,
            wind_direction=Session.WindDirection.FROM_LEFT,
            nutrition=Session.Nutrition.GOOD,
            sleep_hours="7.5",
            sleep_notes="Woke up once but fell back asleep quickly",
            stress=Session.Stress.LOW,
            fatigue=Session.Fatigue.MEDIUM,
            physical_sensations="Slight tightness in bow-arm shoulder",
        )
        session.refresh_from_db()
        assert session.time_of_day == "morning"
        assert session.weather == "overcast"
        assert session.temperature_celsius == -5
        assert session.wind_force == 2
        assert session.wind_direction == "from_left"
        assert session.nutrition == 4
        assert float(session.sleep_hours) == 7.5
        assert session.sleep_notes == "Woke up once but fell back asleep quickly"
        assert session.stress == 2
        assert session.fatigue == 3
        assert session.physical_sensations == "Slight tightness in bow-arm shoulder"

    def test_temperature_celsius_accepts_negative_values(self):
        """Finland winter test: negative temperatures must be storable."""
        session = SessionFactory(temperature_celsius=-20)
        session.refresh_from_db()
        assert session.temperature_celsius == -20

    def test_sleep_hours_accepts_decimal(self):
        session = SessionFactory(sleep_hours="6.5")
        session.refresh_from_db()
        assert float(session.sleep_hours) == 6.5

    def test_sleep_hours_rejects_negative(self):
        session = SessionFactory(sleep_hours="-1")
        with pytest.raises(ValidationError):
            session.full_clean()

    def test_sleep_hours_rejects_above_24(self):
        session = SessionFactory(sleep_hours="25")
        with pytest.raises(ValidationError):
            session.full_clean()

    def test_sleep_hours_boundary_zero_is_valid(self):
        session = SessionFactory(sleep_hours="0")
        session.full_clean()

    def test_sleep_hours_boundary_24_is_valid(self):
        session = SessionFactory(sleep_hours="24")
        session.full_clean()

    def test_integer_choice_fields_reject_out_of_range(self):
        for field in ("wind_force", "nutrition", "stress", "fatigue"):
            session = SessionFactory(**{field: 6})
            with pytest.raises(ValidationError):
                session.full_clean()

    def test_integer_choice_fields_reject_zero(self):
        for field in ("wind_force", "nutrition", "stress", "fatigue"):
            session = SessionFactory(**{field: 0})
            with pytest.raises(ValidationError):
                session.full_clean()

    def test_weather_rejects_invalid_choice(self):
        session = SessionFactory(weather="hailstorm")
        with pytest.raises(ValidationError):
            session.full_clean()

    def test_wind_direction_rejects_invalid_choice(self):
        session = SessionFactory(wind_direction="north")
        with pytest.raises(ValidationError):
            session.full_clean()

    def test_time_of_day_rejects_invalid_choice(self):
        session = SessionFactory(time_of_day="noon")
        with pytest.raises(ValidationError):
            session.full_clean()
