from django.urls import path
from training.views import home

app_name = "training"

urlpatterns = [path("home/", home, name="home")]
