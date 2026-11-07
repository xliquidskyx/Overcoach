import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError

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
    make_exercise(name="Squat")
    with pytest.raises(IntegrityError):
        make_exercise(name="squat")


@pytest.mark.django_db
def test_deleting_active_exercise_raises_protected_error(
    make_exercise, make_planned_exercise
):
    exercise = make_exercise()
    make_planned_exercise(exercise=exercise)
    with pytest.raises(ProtectedError):
        exercise.delete()
