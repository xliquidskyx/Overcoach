from django.db import transaction, IntegrityError
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
    session = (
        WorkoutSession.objects.filter(user=user, finished_at=None)
        .select_related("planned_day")
        .first()
    )

    return session


def start_session(user):
    """Start a workout session for ``user``, or return the one in progress.

    Returns a ``(session, created)`` tuple, like ``get_or_create``:

    - If the user already has an unfinished session (planned or off-plan),
      return ``(that_session, False)`` and create nothing. This check comes
      first, before the plan is consulted.
    - Otherwise create a session with ``planned_day = next_planned_day(user)``
      and return ``(new_session, True)``. If there is no active block, or the
      active block has no days, ``planned_day`` is ``None`` and the session
      is off-plan (decision 41).

    At most one unfinished session per user is also enforced in the database
    (``workout_session_one_unfinished_per_user``). If a concurrent request
    creates one between the check and the insert, the resulting
    ``IntegrityError`` is caught and the existing session is returned with
    ``created=False``, so a double submit behaves like a single one.

    ``started_at`` comes from the model default (``timezone.now``).
    """

    active_session = unfinished_session(user)

    if active_session is not None:
        return (active_session, False)

    planned_day = next_planned_day(user=user)

    try:
        with transaction.atomic():
            session = WorkoutSession.objects.create(user=user, planned_day=planned_day)
    except IntegrityError:
        session = WorkoutSession.objects.get(user=user, finished_at__isnull=True)
        return (session, False)

    return (session, True)
