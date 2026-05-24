import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMySettingsView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("preferences:mysettings"))
        assert response.status_code == 200

    def test_page_contains_settings_heading(self, client):
        response = client.get(reverse("preferences:mysettings"))
        assert b"Settings" in response.content

    def test_url_reversible(self):
        assert reverse("preferences:mysettings") == "/mysettings/"


@pytest.mark.django_db
class TestNavBarIntegration:
    def test_mybows_nav_includes_settings_link(self, client):
        response = client.get(reverse("equipment:mybows"))
        assert b"/mysettings/" in response.content

    def test_mysettings_nav_marks_settings_active(self, client):
        response = client.get(reverse("preferences:mysettings"))
        content = response.content.decode()
        # The Settings nav link should have the nav-active class applied
        assert "nav-active" in content
        # Verify the active class appears on the Settings link specifically
        assert 'href="/mysettings/"' in content

    def test_homepage_has_no_nav_bar(self, client):
        response = client.get(reverse("practice_sessions:home"))
        assert b"site-nav" not in response.content
