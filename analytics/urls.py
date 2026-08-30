from django.urls import path

from analytics import views

app_name = "analytics"

urlpatterns = [
    path("mystatistics/", views.StatisticsView.as_view(), name="mystatistics"),
]
