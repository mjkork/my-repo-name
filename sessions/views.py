from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from equipment.models import Bow
from preferences.models import UserPreferences
from sessions.forms import SessionForm
from sessions.models import Session


def _paginate_sessions(request: HttpRequest) -> tuple:
    """Return (page_obj, page_range) for the session list."""
    qs = Session.objects.select_related("bow").order_by("-date", "-pk")
    paginator = Paginator(qs, UserPreferences.load().sessions_per_page)
    page_num = request.GET.get("page", 1)
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    page_range = [
        {"ellipsis": True} if num == Paginator.ELLIPSIS
        else {"num": num, "current": num == page.number}
        for num in paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)
    ]
    return page, page_range


class HomeView(TemplateView):
    template_name = "sessions/home.html"

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        totals = Session.objects.aggregate(
            total_sessions=Count("pk"),
            total_arrows=Coalesce(Sum("total_arrows"), 0),
        )
        raw_breakdown = list(
            Session.objects.values("bow__name").annotate(
                sessions_count=Count("pk"),
                arrows_count=Coalesce(Sum("total_arrows"), 0),
            )
        )
        named = sorted(
            [
                {
                    "bow_name": r["bow__name"],
                    "sessions_count": r["sessions_count"],
                    "arrows_count": r["arrows_count"],
                }
                for r in raw_breakdown
                if r["bow__name"] is not None
            ],
            key=lambda x: -x["sessions_count"],
        )
        bowless = [
            {
                "bow_name": "(no bow recorded)",
                "sessions_count": r["sessions_count"],
                "arrows_count": r["arrows_count"],
            }
            for r in raw_breakdown
            if r["bow__name"] is None
        ]
        ctx["total_sessions"] = totals["total_sessions"]
        ctx["total_arrows"] = totals["total_arrows"]
        ctx["per_bow_breakdown"] = named + bowless

        most_recent = Session.objects.order_by("-date", "-pk").first()
        if most_recent is None:
            ctx["next_focus_state"] = "empty"
        elif not most_recent.next_focus:
            ctx["next_focus_state"] = "no_focus"
        else:
            ctx["next_focus_state"] = "has_focus"
            ctx["next_focus_text"] = most_recent.next_focus
            ctx["next_focus_session_date"] = most_recent.date

        return ctx


class MySessionsView(View):
    """List all training sessions; handle Add Session form."""

    template_name = "sessions/mysessions.html"

    def _context(
        self,
        request: HttpRequest,
        session_form: SessionForm,
        modify_session_form: SessionForm | None = None,
        modify_pk: int | None = None,
    ) -> dict:
        page, page_range = _paginate_sessions(request)
        return {
            "sessions":             page,
            "page_range":           page_range,
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
        return render(request, self.template_name, self._context(request, form))

    def post(self, request: HttpRequest) -> HttpResponse:
        session_form = SessionForm(request.POST, prefix="session")
        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.session_type = Session.SessionType.FREE_PRACTICE
            session.save()
            return redirect("practice_sessions:mysessions")
        return render(request, self.template_name, self._context(request, session_form))


class ModifySessionView(View):
    """Edit an existing session."""

    template_name = "sessions/mysessions.html"

    def _full_context(self, request: HttpRequest, pk: int, modify_session_form: SessionForm) -> dict:
        page, page_range = _paginate_sessions(request)
        return {
            "sessions":             page,
            "page_range":           page_range,
            "session_form":         SessionForm(prefix="session"),
            "bows_exist":           Bow.objects.exists(),
            "modify_session_form":  modify_session_form,
            "modify_pk":            pk,
        }

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(Session, pk=pk)
        form = SessionForm(instance=session, prefix="modify")
        return render(request, self.template_name, self._full_context(request, pk, form))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = get_object_or_404(Session, pk=pk)
        form = SessionForm(request.POST, instance=session, prefix="modify")
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated.")
            return redirect("practice_sessions:mysessions")
        return render(request, self.template_name, self._full_context(request, pk, form))


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
