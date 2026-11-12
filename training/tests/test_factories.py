import pytest

from django.contrib.auth import get_user_model

from training.models import Exercise, Measurement, Profile, SetLog, PlannedDay, PlannedExercise, WorkoutSession

User = get_user_model()


@pytest.mark.django_db
def test_make_user_create_distinct_objects(make_user):
    first_user = make_user()
    second_user = make_user()

    assert first_user.pk != second_user.pk
    assert User.objects.count() == 2


@pytest.mark.django_db
def test_make_profile_builds_its_own_user(make_profile):
    make_profile()
    make_profile()

    assert Profile.objects.count() == 2
    assert User.objects.count() == 2


@pytest.mark.django_db
def test_make_exercise_create_distinct_objects(make_exercise):
    first_exercise = make_exercise()
    second_exercise = make_exercise()

    assert first_exercise.pk != second_exercise.pk
    assert Exercise.objects.count() == 2


@pytest.mark.django_db
def test_make_day_create_distinct_objects(make_day):
    first_day = make_day()
    second_day = make_day()

    assert first_day.pk != second_day.pk
    assert PlannedDay.objects.count() == 2


@pytest.mark.django_db
def test_make_planned_exercise_create_distinct_objects(make_planned_exercise):
    first_planned_exercise = make_planned_exercise()
    second_planned_exercise = make_planned_exercise()

    assert first_planned_exercise.pk != second_planned_exercise.pk
    assert PlannedExercise.objects.count() == 2

@pytest.mark.django_db
def test_factories_create_valid_objects(make_session, make_set_log, make_measurement):
    session = make_session()
    make_set_log(session=session)
    make_set_log(session=session)
    measurement = make_measurement(user=session.user)

    for obj in (session, measurement, *session.sets.all()):
        obj.full_clean()

    assert WorkoutSession.objects.count() == 1
    assert SetLog.objects.count() == 2
    assert Measurement.objects.count() == 1