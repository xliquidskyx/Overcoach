from django.urls import path
from . import views

app_name = "training"

urlpatterns = [
    path("today/", views.today, name="today"),
    path("onboarding/", views.onboarding, name="onboarding"),
]
