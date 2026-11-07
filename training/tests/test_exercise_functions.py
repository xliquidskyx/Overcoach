import datetime
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError
from training.models import PlannedExercise, PlannedDay, Exercise

User = get_user_model()


@pytest.mark.django_db
def test_exercise_name_must_be_unique(make_exercise):
    make_exercise(name="Squat")
    with pytest.raises(IntegrityError):
        make_exercise(name="Squat")


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="Case-insensitive uniqueness of exercise names is not enforced yet (decisions.md #10).",
    strict=True,
    raises=pytest.fail.Exception,
)
def test_exercise_name_is_unique_no_matter_case(make_exercise):
    make_exercise()
    with pytest.raises(IntegrityError):
        make_exercise(name="squat")


@pytest.mark.django_db
def test_planned_days_with_the_same_position_raise_error(make_block, make_day):
    block = make_block()
    make_day(training_block=block, position=1)
    with pytest.raises(IntegrityError):
        make_day(training_block=block, position=1)


@pytest.mark.django_db
def test_training_block_end_date_lt_start_date_raises_error(make_block):
    with pytest.raises(IntegrityError):
        make_block(
            start_date=datetime.date(2026, 11, 11), end_date=datetime.date(2026, 10, 10)
        )


@pytest.mark.django_db
def test_planned_exercise_reps_max_lt_reps_min_raises_error(make_planned_exercise):
    with pytest.raises(IntegrityError):
        make_planned_exercise(reps_min=10, reps_max=8)


@pytest.mark.django_db
def test_planned_exercise_equal_rep_min_rep_max_create_object(make_planned_exercise):
    make_planned_exercise(reps_min=10, reps_max=10)


@pytest.mark.django_db
def test_deleting_active_exercise_raises_protected_error(
    make_exercise, make_planned_exercise
):
    exercise = make_exercise()
    make_planned_exercise(exercise=exercise)
    with pytest.raises(ProtectedError):
        exercise.delete()


@pytest.mark.django_db
def test_deleting_block_deletes_objects_cascade(make_planned_exercise):
    planned_exercise = make_planned_exercise()
    day = planned_exercise.planned_day
    block = day.training_block
    user = block.user
    exercise = planned_exercise.exercise

    block.delete()

    assert PlannedDay.objects.filter(pk=day.pk).exists() == False
    assert PlannedExercise.objects.filter(pk=planned_exercise.pk).exists() == False
    assert User.objects.filter(pk=user.pk).exists() == True
    assert Exercise.objects.filter(pk=exercise.pk).exists() == True


@pytest.mark.django_db
def test_block_days_are_ordered_by_position(make_block, make_day):
    block = make_block()
    third_day = make_day(training_block=block, position=3)
    second_day = make_day(training_block=block, position=2)
    first_day = make_day(training_block=block, position=1)

    assert list(block.days.all()) == [first_day, second_day, third_day]


@pytest.mark.django_db
def test_two_actvie_training_blocks_for_user_raise_error(make_block):
    block = make_block(is_active=True)
    user = block.user
    with pytest.raises(IntegrityError):
        make_block(user=user, is_active=True)


@pytest.mark.django_db
def test_active_and_inactive_block_for_one_user_do_not_raise_error(make_block):
    block = make_block(is_active=True)
    user = block.user
    make_block(user=user)


@pytest.mark.django_db
def test_two_inactive_block_for_one_user_do_not_raise_error(make_block):
    block = make_block()
    user = block.user
    make_block(user=user)


@pytest.mark.django_db
def test_two_active_blocks_for_two_distinct_users_do_not_raise_error(make_block):
    make_block(is_active=True)
    make_block(is_active=True)


@pytest.mark.django_db
def test_planned_exercise_none_rpe_creates_object(make_planned_exercise):
    make_planned_exercise(rpe=None)


@pytest.mark.django_db
def test_planned_exercise_rpe_range(make_planned_exercise):
    make_planned_exercise(rpe=0)
    make_planned_exercise(rpe=10)


@pytest.mark.django_db
def test_planned_exercise_rpe_gt_ten_raises_error(make_planned_exercise):
    with pytest.raises(IntegrityError):
        make_planned_exercise(rpe=10.5)


@pytest.mark.django_db
def test_planned_exercise_zero_sets_raises_error(make_planned_exercise):
    with pytest.raises(IntegrityError):
        make_planned_exercise(sets=0)


@pytest.mark.django_db
def test_planned_exercise_zero_reps_min_raises_error(make_planned_exercise):
    with pytest.raises(IntegrityError):
        make_planned_exercise(reps_min=0)


@pytest.mark.django_db
def test_planned_exercises_sets_and_reps_min_gt_zero_create_object(
    make_planned_exercise,
):
    make_planned_exercise(sets=1, reps_min=1)
