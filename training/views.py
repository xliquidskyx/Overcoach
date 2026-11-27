from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm
from .services import (
    create_profile,
    days_with_exercises,
    has_profile,
    next_planned_day,
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


@login_required
def day_detail(request, pk):
    """One planned day of the user's own plan.

    The day is looked up in days_with_exercises(request.user), so a day
    from another user's block returns 404. Days from inactive blocks are
    included on purpose: they are the user's own history. No profile
    check: a user without a profile has no days, so they get 404 anyway.

    Context:
        day: the PlannedDay with its training block and its exercises
             prefetched in position order. Never None (404 instead).
    """

    day = get_object_or_404(days_with_exercises(request.user), pk=pk)

    return render(request, "training/day_detail.html", {"day": day})
