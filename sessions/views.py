from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from sessions.models import Session


class HomeView(TemplateView):
    template_name = "sessions/home.html"


class MySessionsView(View):
    """List all training sessions ordered by date descending."""

    template_name = "sessions/mysessions.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {
            "sessions": Session.objects.all(),
        })
