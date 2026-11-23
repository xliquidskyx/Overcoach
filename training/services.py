from django.db import transaction
from django.db.models import Prefetch
from .models import Profile, PlannedDay, PlannedExercise, TrainingBlock, WorkoutSession


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


def next_planned_day(user):
    active_block = TrainingBlock.objects.filter(user=user, is_active=True).first()
    if active_block is None:
        return None

    first_day = active_block.days.first()
    last_session = (
        WorkoutSession.objects.filter(
            user=user, planned_day__training_block=active_block
        )
        .select_related("planned_day")
        .first()
    )

    if last_session is None:
        return first_day

    if last_session.finished_at is None:
        return last_session.planned_day

    next_day = active_block.days.filter(
        position__gt=last_session.planned_day.position
    ).first()

    if next_day is None:
        return first_day

    return next_day


def days_with_exercises(user):
    return (
        PlannedDay.objects.filter(training_block__user=user)
        .select_related("training_block")
        .prefetch_related(
            Prefetch(
                "exercises",
                queryset=PlannedExercise.objects.select_related("exercise").order_by(
                    "position"
                ),
            )
        )
    )


def unfinished_session(user):
    session = WorkoutSession.objects.filter(user=user, finished_at=None).first()

    return session
