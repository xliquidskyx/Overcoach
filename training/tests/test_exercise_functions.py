import pytest
from training.models import Exercise
from django.db import IntegrityError


@pytest.mark.django_db
def test_exercise_name_must_be_unique():
    Exercise.objects.create(name="Squat", category=Exercise.Category.SQUAT)

    with pytest.raises(IntegrityError):
        Exercise.objects.create(name="Squat", category=Exercise.Category.SQUAT)


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="Case-insensitive uniqueness of exercise names is not enforced yet (decisions.md #12).",
    strict=True,
    raises=pytest.fail.Exception,
)
def test_exercise_name_is_unique_no_matter_case():
    Exercise.objects.create(name="Squat", category=Exercise.Category.SQUAT)

    with pytest.raises(IntegrityError):
        Exercise.objects.create(name="squat", category=Exercise.Category.SQUAT)
