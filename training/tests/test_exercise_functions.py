import pytest
from django.db import IntegrityError


@pytest.mark.django_db
def test_exercise_name_must_be_unique(make_exercise):
    make_exercise()
    with pytest.raises(IntegrityError):
        make_exercise()


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
