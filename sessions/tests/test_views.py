import datetime

import pytest
from django.urls import reverse

from equipment.tests.factories import BowFactory
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
        SessionFactory(bow=bow, arrow_count=10)
        SessionFactory(bow=bow, arrow_count=15)
        SessionFactory(bow=bow, arrow_count=None)
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
        SessionFactory.create_batch(3, bow=bow1, arrow_count=10)
        SessionFactory(bow=bow2, arrow_count=5)
        response = client.get(reverse("practice_sessions:home"))
        breakdown = response.context["per_bow_breakdown"]
        assert len(breakdown) == 2
        assert breakdown[0]["bow_name"] == bow1.name
        assert breakdown[0]["sessions_count"] == 3
        assert breakdown[1]["bow_name"] == bow2.name
        assert breakdown[1]["sessions_count"] == 1

    def test_no_bow_sessions(self, client):
        SessionFactory(bow=None, arrow_count=20)
        SessionFactory(bow=None, arrow_count=10)
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
        SessionFactory.create_batch(2, bow=bow, arrow_count=10)
        SessionFactory(bow=None, arrow_count=5)
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
