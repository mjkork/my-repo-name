import datetime

import pytest
from django.urls import reverse

from sessions.tests.factories import SessionFactory

URL = "/mysessions/"


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

    def test_page_one_shows_ten_sessions(self, client):
        SessionFactory.create_batch(15)
        response = client.get(reverse("practice_sessions:mysessions"))
        assert len(response.context["sessions"]) == 10

    def test_page_two_shows_remaining_sessions(self, client):
        SessionFactory.create_batch(15)
        response = client.get(reverse("practice_sessions:mysessions") + "?page=2")
        assert len(response.context["sessions"]) == 5

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
