from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from equipment.models import Bow
from sessions.forms import SessionForm
from sessions.models import Session


class HomeView(TemplateView):
    template_name = "sessions/home.html"


class MySessionsView(View):
    """List all training sessions; handle Add Session form."""

    template_name = "sessions/mysessions.html"

    def _context(self, session_form: SessionForm) -> dict:
        return {
            "sessions":    Session.objects.select_related("bow").all(),
            "session_form": session_form,
            "bows_exist":  Bow.objects.exists(),
        }

    def get(
        self,
        request: HttpRequest,
        session_form: SessionForm | None = None,
    ) -> HttpResponse:
        return render(
            request,
            self.template_name,
            self._context(session_form or SessionForm(prefix="session")),
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        session_form = SessionForm(request.POST, prefix="session")
        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.session_type = Session.SessionType.FREE_PRACTICE
            session.save()
            return redirect("practice_sessions:mysessions")
        return render(request, self.template_name, self._context(session_form))
