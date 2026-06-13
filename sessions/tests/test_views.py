import datetime

import pytest
from django.urls import reverse

from equipment.tests.factories import BowFactory
from preferences.models import UserPreferences
from sessions.tests.factories import SessionFactory

URL = "/mysessions/"


@pytest.mark.django_db
class TestHomeViewStats:
    def test_zero_state(self, client):
        response = client.get(reverse("practice_sessions:home"))
        assert response.status_code == 200
        assert response.context["total_sessions"] == 0
        assert response.context["total_arrows"] == 0
        assert response.context["per_bow_breakdown"] == []

    def test_single_bow_with_sessions(self, client):
        bow = BowFactory()
        SessionFactory(bow=bow, total_arrows=10)
        SessionFactory(bow=bow, total_arrows=15)
        SessionFactory(bow=bow, total_arrows=None)
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["total_sessions"] == 3
        assert response.context["total_arrows"] == 25
        breakdown = response.context["per_bow_breakdown"]
        assert len(breakdown) == 1
        assert breakdown[0]["bow_name"] == bow.name
        assert breakdown[0]["sessions_count"] == 3
        assert breakdown[0]["arrows_count"] == 25

    def test_multiple_bows_sorted_by_sessions_desc(self, client):
        bow1 = BowFactory()
        bow2 = BowFactory()
        SessionFactory.create_batch(3, bow=bow1, total_arrows=10)
        SessionFactory(bow=bow2, total_arrows=5)
        response = client.get(reverse("practice_sessions:home"))
        breakdown = response.context["per_bow_breakdown"]
        assert len(breakdown) == 2
        assert breakdown[0]["bow_name"] == bow1.name
        assert breakdown[0]["sessions_count"] == 3
        assert breakdown[1]["bow_name"] == bow2.name
        assert breakdown[1]["sessions_count"] == 1

    def test_no_bow_sessions(self, client):
        SessionFactory(bow=None, total_arrows=20)
        SessionFactory(bow=None, total_arrows=10)
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["total_sessions"] == 2
        assert response.context["total_arrows"] == 30
        breakdown = response.context["per_bow_breakdown"]
        assert len(breakdown) == 1
        assert breakdown[0]["bow_name"] == "(no bow recorded)"
        assert breakdown[0]["sessions_count"] == 2
        assert breakdown[0]["arrows_count"] == 30

    def test_mixed_bows_and_no_bow(self, client):
        bow = BowFactory()
        SessionFactory.create_batch(2, bow=bow, total_arrows=10)
        SessionFactory(bow=None, total_arrows=5)
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["total_sessions"] == 3
        assert response.context["total_arrows"] == 25
        breakdown = response.context["per_bow_breakdown"]
        assert len(breakdown) == 2
        assert breakdown[0]["bow_name"] == bow.name
        assert breakdown[-1]["bow_name"] == "(no bow recorded)"


@pytest.mark.django_db
class TestMySessionsViewPagination:
    def test_few_sessions_all_on_page_one(self, client):
        SessionFactory.create_batch(5)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert response.status_code == 200
        assert len(response.context["sessions"]) == 5

    def test_few_sessions_no_other_pages(self, client):
        SessionFactory.create_batch(5)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert not response.context["sessions"].has_other_pages()

    def test_eight_sessions_no_pagination(self, client):
        SessionFactory.create_batch(8)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert not response.context["sessions"].has_other_pages()

    def test_nine_sessions_triggers_pagination(self, client):
        SessionFactory.create_batch(9)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert response.context["sessions"].has_other_pages()

    def test_page_one_shows_eight_sessions(self, client):
        SessionFactory.create_batch(15)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert len(response.context["sessions"]) == 8

    def test_page_two_shows_remaining_sessions(self, client):
        SessionFactory.create_batch(15)
        response = client.get(reverse("practice_sessions:mysessions") + "?page=2")
        assert len(response.context["sessions"]) == 7

    def test_page_one_is_most_recent_by_date(self, client):
        base = datetime.date(2025, 1, 1)
        for i in range(15):
            SessionFactory(date=base + datetime.timedelta(days=i))
        response = client.get(reverse("practice_sessions:mysessions"))
        page_sessions = list(response.context["sessions"])
        dates = [s.date for s in page_sessions]
        assert dates == sorted(dates, reverse=True)
        assert dates[0] == base + datetime.timedelta(days=14)

    def test_invalid_page_number_returns_200(self, client):
        SessionFactory.create_batch(5)
        response = client.get(reverse("practice_sessions:mysessions") + "?page=999")
        assert response.status_code == 200

    def test_invalid_page_string_returns_200(self, client):
        SessionFactory.create_batch(5)
        response = client.get(reverse("practice_sessions:mysessions") + "?page=garbage")
        assert response.status_code == 200


@pytest.mark.django_db
class TestSessionQuickDeleteRendering:
    def test_trash_button_has_delete_url(self, client):
        session = SessionFactory()
        response = client.get(reverse("practice_sessions:mysessions"))
        expected = reverse("practice_sessions:deletesession", kwargs={"pk": session.pk})
        assert expected.encode() in response.content

    def test_trash_button_has_delete_name(self, client):
        SessionFactory(name="Morning practice")
        response = client.get(reverse("practice_sessions:mysessions"))
        assert b'data-delete-name="Morning practice"' in response.content

    def test_trash_button_has_delete_label(self, client):
        SessionFactory()
        response = client.get(reverse("practice_sessions:mysessions"))
        assert b'data-delete-label="session"' in response.content

    def test_trash_button_has_date_context(self, client):
        SessionFactory(date=datetime.date(2025, 5, 15))
        response = client.get(reverse("practice_sessions:mysessions"))
        assert b'data-delete-context="15 May 2025"' in response.content


@pytest.mark.django_db
class TestHomeViewNextFocus:
    def test_no_sessions_empty_state(self, client):
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["next_focus_state"] == "empty"
        assert "next_focus_text" not in response.context

    def test_sessions_but_no_focus_set(self, client):
        SessionFactory(next_focus="")
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["next_focus_state"] == "no_focus"
        assert "next_focus_text" not in response.context

    def test_most_recent_has_focus(self, client):
        session = SessionFactory(next_focus="Work on follow-through")
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["next_focus_state"] == "has_focus"
        assert response.context["next_focus_text"] == "Work on follow-through"
        assert response.context["next_focus_session_date"] == session.date

    def test_only_most_recent_session_used(self, client):
        SessionFactory(date=datetime.date(2025, 1, 1), next_focus="Work on stance")
        SessionFactory(date=datetime.date(2025, 1, 2), next_focus="Work on anchor")
        response = client.get(reverse("practice_sessions:home"))
        assert response.context["next_focus_text"] == "Work on anchor"


@pytest.mark.django_db
class TestSessionListPaginationRespectsPreference:
    def test_default_page_size_is_8(self, client):
        SessionFactory.create_batch(10)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert len(response.context["sessions"]) == 8

    def test_page_size_5_limits_to_5_per_page(self, client):
        UserPreferences.objects.create(pk=1, sessions_per_page=5)
        SessionFactory.create_batch(7)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert len(response.context["sessions"]) == 5

    def test_page_size_10_shows_10_on_page_one(self, client):
        UserPreferences.objects.create(pk=1, sessions_per_page=10)
        SessionFactory.create_batch(12)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert len(response.context["sessions"]) == 10


@pytest.mark.django_db
class TestSessionFormSections:
    """Template renders five section headings; all fields present in HTML."""

    def _html(self, client: object) -> str:
        return client.get(reverse("practice_sessions:mysessions")).content.decode()

    def test_all_five_section_headings_are_rendered(self, client):
        html = self._html(client)
        for heading in ("Session basics", "Shooting details", "Conditions", "How you felt", "Reflection"):
            assert heading in html, f"Section heading '{heading}' not found in rendered page"

    def test_outdoor_only_fields_present_in_dom_when_indoor(self, client):
        """Outdoor fields are hidden via JS/CSS, not removed — they must be in the DOM."""
        html = self._html(client)
        for field_name in ("weather", "temperature_celsius", "wind_force", "wind_direction"):
            assert f'name="session-{field_name}"' in html, (
                f"Field '{field_name}' missing from DOM — it should be hidden visually, not absent"
            )

    def test_data_outdoor_only_attribute_present_on_four_fields(self, client):
        """The four outdoor-only wrappers must carry data-outdoor-only for JS to find them."""
        html = self._html(client)
        assert html.count("data-outdoor-only") == 8  # 4 in Add modal + 4 in Modify modal

    def test_form_accepts_all_subjective_fields_filled(self, client):
        """Regression: section wrappers don't break submission of subjective fields."""
        today = datetime.date.today().isoformat()
        data = {
            "session-name": "Section test",
            "session-date": today,
            "session-location": "outdoor",
            "session-time_of_day": "morning",
            "session-weather": "sunny",
            "session-temperature_celsius": "20",
            "session-wind_force": "2",
            "session-wind_direction": "from_front",
            "session-nutrition": "4",
            "session-sleep_hours": "7.5",
            "session-stress": "2",
            "session-fatigue": "3",
        }
        response = client.post(reverse("practice_sessions:mysessions"), data)
        assert response.status_code == 302, f"Expected redirect, got {response.status_code}"

    def test_form_accepts_all_subjective_fields_blank(self, client):
        """Regression: blank subjective fields still produce a valid session."""
        today = datetime.date.today().isoformat()
        data = {
            "session-name": "Minimal section test",
            "session-date": today,
            "session-location": "indoor",
        }
        response = client.post(reverse("practice_sessions:mysessions"), data)
        assert response.status_code == 302, f"Expected redirect, got {response.status_code}"
