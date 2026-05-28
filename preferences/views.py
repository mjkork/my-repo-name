from io import StringIO

from django.core.management import call_command
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View


class MySettingsView(View):
    """Settings page; hosts backup management and future config features."""

    template_name = "preferences/mysettings.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name)


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
