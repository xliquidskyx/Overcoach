import pytest
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from training.models import Exercise, Measurement, PlannedDay, SetLog, WorkoutSession

User = get_user_model()


def test_deleting_block_leaves_session_and_sets_day_as_none(make_day, make_session):
    planned_day = make_day()
    session = make_session(planned_day=planned_day)

    planned_day.training_block.delete()
    session.refresh_from_db()

    assert WorkoutSession.objects.filter(pk=session.pk).exists()
    assert session.planned_day is None
    assert not PlannedDay.objects.filter(pk=planned_day.pk).exists()


def test_deleting_user_deletes_all_their_session_data(
    make_session, make_set_log, make_measurement
):
    session = make_session()
    set_log = make_set_log(session=session)
    measurement = make_measurement(user=session.user)
    exercise = set_log.exercise

    session.user.delete()

    assert not WorkoutSession.objects.filter(pk=session.pk).exists()
    assert not Measurement.objects.filter(pk=measurement.pk).exists()
    assert not SetLog.objects.filter(pk=set_log.pk).exists()
    assert Exercise.objects.filter(pk=exercise.pk).exists()


def test_deleting_exercise_with_set_log_raises_error(make_set_log):
    set_log = make_set_log()
    exercise = set_log.exercise

    with pytest.raises(ProtectedError):
        exercise.delete()

    assert Exercise.objects.filter(pk=exercise.pk).exists()
    assert SetLog.objects.filter(pk=set_log.pk).exists()


def test_deleting_exercise_without_set_log_is_successful(make_exercise):
    exercise = make_exercise()
    exercise.delete()

    assert not Exercise.objects.filter(pk=exercise.pk).exists()


def test_deleting_user_a_does_not_delete_user_b_session(make_session, make_measurement):
    session_a = make_session()
    session_b = make_session()
    measurement_a = make_measurement(user=session_a.user)
    measurement_b = make_measurement(user=session_b.user)
    user_pk_a = session_a.user.pk
    user_pk_b = session_b.user.pk

    session_a.user.delete()

    assert not User.objects.filter(pk=user_pk_a).exists()
    assert not WorkoutSession.objects.filter(pk=session_a.pk).exists()
    assert not Measurement.objects.filter(pk=measurement_a.pk).exists()

    assert User.objects.filter(pk=user_pk_b).exists()
    assert WorkoutSession.objects.filter(pk=session_b.pk).exists()
    assert Measurement.objects.filter(pk=measurement_b.pk).exists()
