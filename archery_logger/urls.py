from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("sessions.urls", namespace="practice_sessions")),
    path("", include("equipment.urls")),
    path("", include("preferences.urls")),
]
