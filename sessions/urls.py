from django.urls import path

from sessions.views import HomeView, MySessionsView

app_name = "practice_sessions"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("mysessions/", MySessionsView.as_view(), name="mysessions"),
]
