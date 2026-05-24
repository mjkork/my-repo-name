from django.urls import path

from preferences.views import MySettingsView

app_name = "preferences"

urlpatterns = [
    path("mysettings/", MySettingsView.as_view(), name="mysettings"),
]
