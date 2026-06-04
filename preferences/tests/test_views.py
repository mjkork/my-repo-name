import json

import pytest
from django.urls import reverse
from django.utils import timezone

from equipment.tests.factories import BowFactory
from preferences.models import UserPreferences
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

    def test_manage_page_properties_card_present(self, client):
        response = client.get(reverse("preferences:mysettings"))
        assert b"Manage page properties" in response.content

    def test_sessions_per_page_dropdown_present(self, client):
        response = client.get(reverse("preferences:mysettings"))
        content = response.content.decode()
        for value in range(5, 11):
            assert f'value="{value}"' in content


@pytest.mark.django_db
class TestNavBarIntegration:
    def test_mybows_nav_includes_settings_link(self, client):
        response = client.get(reverse("equipment:mybows"))
        assert b"/mysettings/" in response.content

    def test_mysettings_nav_marks_settings_active(self, client):
        response = client.get(reverse("preferences:mysettings"))
        content = response.content.decode()
        assert "nav-active" in content
        assert 'href="/mysettings/"' in content

    def test_homepage_has_no_nav_bar(self, client):
        response = client.get(reverse("practice_sessions:home"))
        assert b"site-nav" not in response.content


@pytest.mark.django_db
class TestUserPreferencesModel:
    def test_load_creates_row_with_default_on_first_call(self):
        assert UserPreferences.objects.count() == 0
        prefs = UserPreferences.load()
        assert prefs.sessions_per_page == 8
        assert UserPreferences.objects.count() == 1

    def test_load_returns_existing_row(self):
        UserPreferences.objects.create(pk=1, sessions_per_page=7)
        prefs = UserPreferences.load()
        assert prefs.sessions_per_page == 7
        assert UserPreferences.objects.count() == 1

    def test_save_with_different_pk_still_results_in_pk_1(self):
        prefs = UserPreferences(pk=2, sessions_per_page=6)
        prefs.save()
        assert UserPreferences.objects.count() == 1
        assert UserPreferences.objects.get().pk == 1

    def test_validator_rejects_value_below_5(self):
        from django.core.exceptions import ValidationError

        prefs = UserPreferences(sessions_per_page=4)
        with pytest.raises(ValidationError):
            prefs.full_clean()

    def test_validator_rejects_value_above_10(self):
        from django.core.exceptions import ValidationError

        prefs = UserPreferences(sessions_per_page=11)
        with pytest.raises(ValidationError):
            prefs.full_clean()


@pytest.mark.django_db
class TestUpdatePreferencesView:
    def test_post_valid_value_updates_and_redirects(self, client):
        response = client.post(
            reverse("preferences:update"), {"sessions_per_page": "5"}
        )
        assert response.status_code == 302
        assert response["Location"] == "/mysettings/"
        assert UserPreferences.load().sessions_per_page == 5

    def test_post_invalid_value_does_not_update(self, client):
        UserPreferences.objects.create(pk=1, sessions_per_page=8)
        response = client.post(
            reverse("preferences:update"), {"sessions_per_page": "100"}
        )
        assert response.status_code == 302
        assert UserPreferences.load().sessions_per_page == 8

    def test_get_returns_405(self, client):
        response = client.get(reverse("preferences:update"))
        assert response.status_code == 405

    def test_url_reversible(self):
        assert reverse("preferences:update") == "/mysettings/preferences/update/"


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
