from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm
from .services import create_profile, has_profile


@login_required
def home(request):
    if not has_profile(request.user):
        return redirect("training:onboarding")
    return render(request, "training/home.html")


@login_required
def onboarding(request):
    if has_profile(request.user):
        return redirect("training:home")

    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            create_profile(request.user, **form.cleaned_data)
            return redirect("training:home")
    else:
        form = ProfileForm()

    return render(request, "training/onboarding.html", {"form": form})
