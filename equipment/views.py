from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from equipment.forms import BowForm, OlympicBowSetupForm
from equipment.models import Bow


class MyBowsView(View):
    """List all bows; handle Add Bow form (creates Bow + OlympicBowSetup together)."""

    template_name = "equipment/mybows.html"

    def get(
        self,
        request: HttpRequest,
        bow_form: BowForm | None = None,
        setup_form: OlympicBowSetupForm | None = None,
    ) -> HttpResponse:
        return render(request, self.template_name, {
            "bows":       Bow.objects.select_related("olympic_setup").all(),
            "bow_form":   bow_form   or BowForm(prefix="bow"),
            "setup_form": setup_form or OlympicBowSetupForm(prefix="setup"),
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        bow_form   = BowForm(request.POST, prefix="bow")
        setup_form = OlympicBowSetupForm(request.POST, prefix="setup")
        if bow_form.is_valid() and setup_form.is_valid():
            bow = bow_form.save()
            setup = setup_form.save(commit=False)
            setup.bow = bow
            setup.save()
            return redirect("equipment:mybows")
        return self.get(request, bow_form=bow_form, setup_form=setup_form)
