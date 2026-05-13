from django.urls import path

from equipment.views import ModifyBowView, MyBowsView

app_name = "equipment"

urlpatterns = [
    path("mybows/", MyBowsView.as_view(), name="mybows"),
    path("mybows/<int:pk>/modify/", ModifyBowView.as_view(), name="modifybow"),
]
