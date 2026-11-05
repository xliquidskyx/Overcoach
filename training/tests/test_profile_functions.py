import pytest
import datetime
from training.models import Profile, Exercise
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


@pytest.mark.django_db
def test_user_cannot_have_two_profiles():
    user = User.objects.create_user(
        username="Laura", email="laura@example.com", password="strongpassword"
    )
    Profile.objects.create(
        user=user,
        date_of_birth=datetime.date(2002, 5, 4),
        goal=Profile.Goal.HYPERTROPHY,
        level=Profile.Level.ADVANCED,
    )

    with pytest.raises(IntegrityError):
        Profile.objects.create(
            user=user,
            date_of_birth=datetime.date(2000, 6, 2),
            goal=Profile.Goal.FAT_LOSS,
            level=Profile.Level.BEGINNER,
        )


@pytest.mark.django_db
def test_exercise_exclusion_works_both_ways():
    user = User.objects.create_user(
        username="Laura", email="laura@example.com", password="strongpassword"
    )
    exercise = Exercise.objects.create(name="Squat", category=Exercise.Category.SQUAT)
    profile = Profile.objects.create(
        user=user,
        date_of_birth=datetime.date(2002, 5, 4),
        goal=Profile.Goal.HYPERTROPHY,
        level=Profile.Level.ADVANCED,
    )
    profile.excluded_exercises.add(exercise)

    assert profile in exercise.excluded_by.all()
    assert exercise in profile.excluded_exercises.all()


@pytest.mark.django_db
def test_exclusion_applies_only_to_one_profile():
    user = User.objects.create_user(
        username="Laura", email="laura@example.com", password="strongpassword"
    )
    second_user = User.objects.create_user(
        username="John", email="john@example.com", password="strongpassword"
    )
    exercise = Exercise.objects.create(name="Squat", category=Exercise.Category.SQUAT)
    profile = Profile.objects.create(
        user=user,
        date_of_birth=datetime.date(2002, 5, 4),
        goal=Profile.Goal.HYPERTROPHY,
        level=Profile.Level.ADVANCED,
    )
    second_profile = Profile.objects.create(
        user=second_user,
        date_of_birth=datetime.date(2002, 5, 4),
        goal=Profile.Goal.HYPERTROPHY,
        level=Profile.Level.ADVANCED,
    )
    profile.excluded_exercises.add(exercise)

    assert second_profile not in exercise.excluded_by.all()
    assert exercise not in second_profile.excluded_exercises.all()
