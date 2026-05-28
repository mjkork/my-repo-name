from django.urls import path

from preferences.views import BackupDownloadView, MySettingsView

app_name = "preferences"

urlpatterns = [
    path("mysettings/", MySettingsView.as_view(), name="mysettings"),
    path(
        "mysettings/backup/download/",
        BackupDownloadView.as_view(),
        name="backup_download",
    ),
]
