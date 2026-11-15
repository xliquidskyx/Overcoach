from django.db import transaction
from .models import Profile


@transaction.atomic
def create_profile(
    user, *, goal, level, sex, date_of_birth, height_cm=None, excluded_exercises=()
):
    profile = Profile.objects.create(
        user=user,
        goal=goal,
        level=level,
        sex=sex,
        date_of_birth=date_of_birth,
        height_cm=height_cm,
    )

    profile.excluded_exercises.set(excluded_exercises)

    return profile


def has_profile(user):
    return Profile.objects.filter(user=user).exists()
