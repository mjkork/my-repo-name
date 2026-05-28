import json

import pytest
from django.urls import reverse
from django.utils import timezone

from equipment.tests.factories import BowFactory
from sessions.tests.factories import SessionFactory


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

    def test_manage_backups_card_present(self, client):
        response = client.get(reverse("preferences:mysettings"))
        assert b"Manage Backups" in response.content

    def test_download_backup_link_present(self, client):
        response = client.get(reverse("preferences:mysettings"))
        assert b"Download backup" in response.content
        assert b"/mysettings/backup/download/" in response.content


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


@pytest.mark.django_db
class TestBackupDownloadView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("preferences:backup_download"))
        assert response.status_code == 200

    def test_content_type_is_json(self, client):
        response = client.get(reverse("preferences:backup_download"))
        assert response["Content-Type"] == "application/json"

    def test_content_disposition_is_attachment_with_today(self, client):
        response = client.get(reverse("preferences:backup_download"))
        today = str(timezone.localdate())
        assert "attachment" in response["Content-Disposition"]
        assert today in response["Content-Disposition"]

    def test_filename_follows_convention(self, client):
        response = client.get(reverse("preferences:backup_download"))
        today = str(timezone.localdate())
        expected = f'filename="myshots-backup-{today}.json"'
        assert expected in response["Content-Disposition"]

    def test_backup_contains_bow(self, client):
        BowFactory(name="Test Bow for Backup")
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        bow_entries = [obj for obj in data if obj["model"] == "equipment.bow"]
        assert any(
            entry["fields"]["name"] == "Test Bow for Backup" for entry in bow_entries
        )

    def test_backup_contains_session(self, client):
        SessionFactory(name="Test Session for Backup")
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        session_entries = [
            obj for obj in data if obj["model"] == "practice_sessions.session"
        ]
        assert any(
            entry["fields"]["name"] == "Test Session for Backup"
            for entry in session_entries
        )

    def test_backup_excludes_contenttypes(self, client):
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        models_in_backup = {obj["model"] for obj in data}
        assert not any(m.startswith("contenttypes.") for m in models_in_backup)

    def test_backup_excludes_auth_permission(self, client):
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        models_in_backup = {obj["model"] for obj in data}
        assert "auth.permission" not in models_in_backup

    def test_backup_excludes_django_sessions(self, client):
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        models_in_backup = {obj["model"] for obj in data}
        assert not any(m.startswith("sessions.") for m in models_in_backup)

    def test_url_reversible(self):
        assert reverse("preferences:backup_download") == "/mysettings/backup/download/"

    def test_response_is_valid_json(self, client):
        response = client.get(reverse("preferences:backup_download"))
        data = json.loads(response.content)
        assert isinstance(data, list)
