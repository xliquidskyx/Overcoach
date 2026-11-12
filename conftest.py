import datetime
from decimal import Decimal
import itertools
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from training.models import (
    Exercise,
    Profile,
    TrainingBlock,
    Measurement,
    PlannedDay,
    PlannedExercise,
    SetLog,
    WorkoutSession,
)

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
        n = next(_counter)
        data = {
            "name": f"Squat {n}",
            "category": Exercise.Category.SQUAT,
        }
        data.update(kwargs)
        return Exercise.objects.create(**data)

    return _create_exercise


@pytest.fixture
def make_block(db, make_user):
    def _create_block(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        data = {
            "name": "Winter Recomposition",
            "start_date": datetime.date(2026, 11, 1),
            "end_date": datetime.date(2027, 3, 1),
            "is_active": False,
        }
        data.update(kwargs)
        return TrainingBlock.objects.create(**data)

    return _create_block


@pytest.fixture
def make_day(db, make_block):
    def _create_day(**kwargs):
        n = next(_counter)
        if "training_block" not in kwargs:
            kwargs["training_block"] = make_block()
        data = {
            "name": f"Push day {n}",
            "position": n,
        }
        data.update(kwargs)
        return PlannedDay.objects.create(**data)

    return _create_day


@pytest.fixture
def make_planned_exercise(db, make_day, make_exercise):
    def _create_planned_exercise(**kwargs):
        n = next(_counter)
        if "planned_day" not in kwargs:
            kwargs["planned_day"] = make_day()
        if "exercise" not in kwargs:
            kwargs["exercise"] = make_exercise()
        data = {
            "position": n,
            "sets": 3,
            "reps_min": 8,
            "reps_max": 10,
            "weight": Decimal("50.0"),
            "rest_seconds": 120,
        }
        data.update(kwargs)
        return PlannedExercise.objects.create(**data)

    return _create_planned_exercise


@pytest.fixture
def make_session(db, make_user):
    def _create_workout_session(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        data = {
            "started_at": timezone.localdate(),
        }
        data.update(kwargs)
        return WorkoutSession.objects.create(**data)
    
    return _create_workout_session

@pytest.fixture
def make_set_log(db, make_session, make_exercise):
    def _create_set_log(**kwargs):
        n = next(_counter)
        if "session" not in kwargs:
            kwargs["session"] = make_session()
        if "exercise" not in kwargs:
            kwargs["exercise"] = make_exercise()
        data = {
            "set_number": n,
            "reps": 10,
            "weight": Decimal("50.0"),
            "rir": 2,
        }
        data.update(kwargs)
        return SetLog.objects.create(**data)

    return _create_set_log

@pytest.fixture
def make_measurement(db, make_user):
    def _create_measurement(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        data = {
            "date": timezone.localdate(),
            "body_weight": Decimal("65.0"),
        }
        data.update(kwargs)
        return Measurement.objects.create(**data)

    return _create_measurement