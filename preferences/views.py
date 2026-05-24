from django.http import HttpRequest, HttpResponse
from django.views import View
from django.shortcuts import render


class MySettingsView(View):
    """Placeholder settings page; future config features will be added here."""

    template_name = "preferences/mysettings.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name)
