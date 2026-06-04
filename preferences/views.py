from io import StringIO

from django.contrib import messages
from django.core.management import call_command
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from preferences.forms import UserPreferencesForm
from preferences.models import UserPreferences


class MySettingsView(View):
    """Settings page; hosts backup management and future config features."""

    template_name = "preferences/mysettings.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        prefs = UserPreferences.load()
        form = UserPreferencesForm(instance=prefs)
        return render(request, self.template_name, {"preferences_form": form})


class UpdatePreferencesView(View):
    """POST-only: save UserPreferences and redirect back to /mysettings/."""

    def post(self, request: HttpRequest) -> HttpResponse:
        prefs = UserPreferences.load()
        form = UserPreferencesForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, "Page size updated.")
        else:
            messages.error(request, "Invalid value — preferences not saved.")
        return redirect("preferences:mysettings")

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponseNotAllowed(["POST"])


class BackupDownloadView(View):
    """Export all user data as a dated JSON file via dumpdata."""

    def get(self, request: HttpRequest) -> HttpResponse:
        buf = StringIO()
        call_command(
            "dumpdata",
            exclude=["contenttypes", "auth.permission", "sessions"],
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            stdout=buf,
        )
        filename = f"myshots-backup-{timezone.localdate()}.json"
        response = HttpResponse(buf.getvalue(), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
