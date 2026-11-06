import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


@pytest.mark.django_db
def test_user_cannot_have_two_profiles(make_user, make_profile):
    user = make_user()
    make_profile(user=user)

    with pytest.raises(IntegrityError):
        make_profile(user=user)


@pytest.mark.django_db
def test_exercise_exclusion_works_both_ways(make_exercise, make_profile):
    exercise = make_exercise()
    profile = make_profile()
    profile.excluded_exercises.add(exercise)

    assert profile in exercise.excluded_by.all()
    assert exercise in profile.excluded_exercises.all()


@pytest.mark.django_db
def test_exclusion_applies_only_to_one_profile(make_user, make_exercise, make_profile):
    user = make_user()
    exercise = make_exercise()
    profile = make_profile()
    second_profile = make_profile(user=user)
    profile.excluded_exercises.add(exercise)

    assert second_profile not in exercise.excluded_by.all()
    assert exercise not in second_profile.excluded_exercises.all()
