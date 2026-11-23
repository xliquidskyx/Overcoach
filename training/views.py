from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm
from .services import (
    create_profile,
    has_profile,
    next_planned_day,
    days_with_exercises,
    unfinished_session,
)


@login_required
def today(request):
    """Start page: what the user should do today.

    Context:
        session: the user's unfinished WorkoutSession, or None.
        day: the next PlannedDay with exercises prefetched in position
             order, or None. Always None when session is set.
    """
    if not has_profile(request.user):
        return redirect("training:onboarding")

    session = unfinished_session(user=request.user)

    if session:
        return render(request, "training/today.html", {"session": session, "day": None})

    day = next_planned_day(user=request.user)

    if day:
        day = days_with_exercises(request.user).get(pk=day.pk)

    return render(request, "training/today.html", {"session": None, "day": day})


@login_required
def onboarding(request):
    if has_profile(request.user):
        return redirect("training:today")

    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            create_profile(request.user, **form.cleaned_data)
            return redirect("training:today")
    else:
        form = ProfileForm()

    return render(request, "training/onboarding.html", {"form": form})
