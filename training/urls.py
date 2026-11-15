from django.urls import path
from . import views

app_name = "training"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("onboarding/", views.onboarding, name="onboarding"),
]
