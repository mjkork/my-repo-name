from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from equipment.forms import BowForm, OlympicBowSetupForm
from equipment.models import Bow, OlympicBowSetup


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
            "bows":              Bow.objects.select_related("olympic_setup").all(),
            "bow_form":          bow_form   or BowForm(prefix="bow"),
            "setup_form":        setup_form or OlympicBowSetupForm(prefix="setup"),
            "modify_bow_form":   BowForm(prefix="modify"),
            "modify_setup_form": OlympicBowSetupForm(prefix="modsetup"),
            "modify_pk":         None,
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


class ModifyBowView(View):
    """Edit an existing bow and its OlympicBowSetup in place."""

    template_name = "equipment/mybows.html"

    def _get_bow(self, pk: int) -> Bow:
        return get_object_or_404(Bow.objects.select_related("olympic_setup"), pk=pk)

    def _full_context(
        self,
        request: HttpRequest,
        pk: int,
        modify_bow_form: BowForm,
        modify_setup_form: OlympicBowSetupForm,
    ) -> dict:
        return {
            "bows":              Bow.objects.select_related("olympic_setup").all(),
            "bow_form":          BowForm(prefix="bow"),
            "setup_form":        OlympicBowSetupForm(prefix="setup"),
            "modify_bow_form":   modify_bow_form,
            "modify_setup_form": modify_setup_form,
            "modify_pk":         pk,
        }

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        bow = self._get_bow(pk)
        setup, _ = OlympicBowSetup.objects.get_or_create(bow=bow)
        return render(request, self.template_name, self._full_context(
            request, pk,
            modify_bow_form=BowForm(instance=bow, prefix="modify"),
            modify_setup_form=OlympicBowSetupForm(instance=setup, prefix="modsetup"),
        ))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        bow = self._get_bow(pk)
        setup, _ = OlympicBowSetup.objects.get_or_create(bow=bow)
        modify_bow_form   = BowForm(request.POST, instance=bow, prefix="modify")
        modify_setup_form = OlympicBowSetupForm(request.POST, instance=setup, prefix="modsetup")
        if modify_bow_form.is_valid() and modify_setup_form.is_valid():
            modify_bow_form.save()
            modify_setup_form.save()
            return redirect("equipment:mybows")
        return render(request, self.template_name, self._full_context(
            request, pk,
            modify_bow_form=modify_bow_form,
            modify_setup_form=modify_setup_form,
        ))


class DeleteBowView(View):
    """Delete a bow. POST only — GET returns 405."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        bow = get_object_or_404(Bow, pk=pk)
        bow.delete()
        return redirect("equipment:mybows")

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        return HttpResponseNotAllowed(["POST"])
