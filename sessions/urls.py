from django.urls import path

from sessions.views import (
    DeleteSessionView,
    HomeView,
    ModifySessionView,
    MySessionsView,
)

app_name = "practice_sessions"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("mysessions/", MySessionsView.as_view(), name="mysessions"),
    path(
        "mysessions/<int:pk>/modify/",
        ModifySessionView.as_view(),
        name="modifysession",
    ),
    path(
        "mysessions/<int:pk>/delete/",
        DeleteSessionView.as_view(),
        name="deletesession",
    ),
]
