from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from equipment.forms import BowForm
from equipment.models import Bow


class MyBowsView(View):
    """List all bows and handle the Add Bow form submission."""

    template_name = "equipment/mybows.html"

    def get(self, request: HttpRequest, form: BowForm | None = None) -> HttpResponse:
        return render(request, self.template_name, {
            "bows": Bow.objects.all(),
            "form": form or BowForm(),
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        form = BowForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("equipment:mybows")
        return self.get(request, form=form)
