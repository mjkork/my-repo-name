from django.urls import path

from equipment.views import DeleteBowView, ModifyBowView, MyBowsView

app_name = "equipment"

urlpatterns = [
    path("mybows/", MyBowsView.as_view(), name="mybows"),
    path("mybows/<int:pk>/modify/", ModifyBowView.as_view(), name="modifybow"),
    path("mybows/<int:pk>/delete/", DeleteBowView.as_view(), name="deletebow"),
]
