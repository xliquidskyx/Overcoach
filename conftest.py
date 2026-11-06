import datetime
import itertools
import pytest
from django.contrib.auth import get_user_model
from training.models import Exercise, Profile

_counter = itertools.count(1)
User = get_user_model()


@pytest.fixture
def make_user(db):
    def _create_user(**kwargs):
        n = next(_counter)
        data = {
            "username": f"Laura{n}",
            "email": f"laura{n}@example.com",
            "password": "strongpassword",
        }
        data.update(kwargs)
        return User.objects.create_user(**data)

    return _create_user


@pytest.fixture
def make_profile(db, make_user):
    def _create_profile(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        data = {
            "date_of_birth": datetime.date(2002, 5, 4),
            "goal": Profile.Goal.HYPERTROPHY,
            "level": Profile.Level.ADVANCED,
        }
        data.update(kwargs)
        return Profile.objects.create(**data)

    return _create_profile


@pytest.fixture
def make_exercise(db):
    def _create_exercise(**kwargs):
        data = {
            "name": "Squat",
            "category": Exercise.Category.SQUAT,
        }
        data.update(kwargs)
        return Exercise.objects.create(**data)

    return _create_exercise
