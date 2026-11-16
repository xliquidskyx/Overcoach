from datetime import date
import pytest
from django.db import IntegrityError
from training.services import create_profile, has_profile
from training.models import Profile

pytestmark = pytest.mark.django_db


def broken_exercises():
    raise RuntimeError("simulated failure")
    yield


def profile_kwargs(**kwargs):
    data = {
        "sex": Profile.Sex.MALE,
        "date_of_birth": date(1999, 5, 3),
        "goal": Profile.Goal.GENERAL_FITNESS,
        "level": Profile.Level.ADVANCED,
    }
    data.update(kwargs)
    return data


def test_create_profile_saves_profile_to_db(make_user):
    user = make_user()
    create_profile(user, **profile_kwargs(height_cm=172))
    profile = Profile.objects.get(user=user)

    assert profile.sex == Profile.Sex.MALE
    assert profile.date_of_birth == date(1999, 5, 3)
    assert profile.goal == Profile.Goal.GENERAL_FITNESS
    assert profile.level == Profile.Level.ADVANCED
    assert profile.height_cm == 172


def test_create_profile_uses_default_values(make_user):
    user = make_user()
    create_profile(user, **profile_kwargs())
    profile = Profile.objects.get(user=user)

    assert profile.height_cm is None
    assert profile.excluded_exercises.count() == 0


def test_create_profile_passes_excluded_exercises_to_db(make_user, make_exercise):
    user = make_user()
    first_exercise = make_exercise()
    second_exercise = make_exercise()
    third_exercise = (
        make_exercise()
    )  # Makes sure that not all exercises are passed with create_profile

    create_profile(
        user,
        **profile_kwargs(excluded_exercises=[first_exercise, second_exercise]),
    )
    profile = Profile.objects.get(user=user)
    excluded = set(profile.excluded_exercises.values_list("pk", flat=True))

    assert excluded == {first_exercise.pk, second_exercise.pk}


def test_create_profile_service_returns_saved_profile(make_user):
    user = make_user()
    profile = create_profile(user, **profile_kwargs())

    assert profile.pk is not None
    assert profile.user == user


def test_duplicate_create_profile_on_user_raises_error(make_user):
    user = make_user()
    create_profile(user, **profile_kwargs())

    with pytest.raises(IntegrityError):
        create_profile(user, **profile_kwargs())


def test_create_profile_rolls_back_when_exclusions_fail(make_user):
    user = make_user()

    with pytest.raises(RuntimeError):
        create_profile(user, **profile_kwargs(excluded_exercises=broken_exercises()))

    assert not Profile.objects.filter(user=user).exists()


def test_has_profile_is_true_only_for_user_with_profile(make_user):
    user = make_user()
    second_user = make_user()

    assert not has_profile(user)
    assert not has_profile(second_user)

    create_profile(user, **profile_kwargs())

    assert has_profile(user)
    assert not has_profile(second_user)
