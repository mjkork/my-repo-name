from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
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

    def _context(
        self,
        session_form: SessionForm,
        modify_session_form: SessionForm | None = None,
        modify_pk: int | None = None,
    ) -> dict:
        return {
            "sessions":             Session.objects.select_related("bow").all(),
            "session_form":         session_form,
            "bows_exist":           Bow.objects.exists(),
            "modify_session_form":  modify_session_form or SessionForm(prefix="modify"),
            "modify_pk":            modify_pk,
        }

    def get(
        self,
        request: HttpRequest,
        session_form: SessionForm | None = None,
    ) -> HttpResponse:
        if session_form is None:
            form = SessionForm(prefix="session")
            # Pre-select the bow from the user's most recent session to save clicks.
            recent_bow_id = (
                Session.objects.filter(bow__isnull=False)
                .order_by("-date", "-pk")
                .values_list("bow_id", flat=True)
                .first()
            )
            if recent_bow_id:
                form.fields["bow"].initial = recent_bow_id
        else:
            form = session_form
        return render(request, self.template_name, self._context(form))

    def post(self, request: HttpRequest) -> HttpResponse:
        session_form = SessionForm(request.POST, prefix="session")
        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.session_type = Session.SessionType.FREE_PRACTICE
            session.save()
            return redirect("practice_sessions:mysessions")
        return render(request, self.template_name, self._context(session_form))


class ModifySessionView(View):
    """Edit an existing session."""

    template_name = "sessions/mysessions.html"

    def _full_context(self, pk: int, modify_session_form: SessionForm) -> dict:
        return {
            "sessions":             Session.objects.select_related("bow").all(),
            "session_form":         SessionForm(prefix="session"),
            "bows_exist":           Bow.objects.exists(),
            "modify_session_form":  modify_session_form,
            "modify_pk":            pk,
        }

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(Session, pk=pk)
        form = SessionForm(instance=session, prefix="modify")
        return render(request, self.template_name, self._full_context(pk, form))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(Session, pk=pk)
        form = SessionForm(request.POST, instance=session, prefix="modify")
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated.")
            return redirect("practice_sessions:mysessions")
        return render(request, self.template_name, self._full_context(pk, form))


class DeleteSessionView(View):
    """Delete a session. POST only — GET returns 405."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(Session, pk=pk)
        session_name = session.name
        session.delete()
        messages.success(request, f"Session '{session_name}' deleted.")
        return redirect("practice_sessions:mysessions")

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        return HttpResponseNotAllowed(["POST"])
