from django.urls import path

from equipment.views import MyBowsView

app_name = "equipment"

urlpatterns = [
    path("mybows/", MyBowsView.as_view(), name="mybows"),
]
