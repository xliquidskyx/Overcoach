import itertools
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from training.models import (
    Exercise,
    Measurement,
    PlannedDay,
    PlannedExercise,
    Profile,
    SetLog,
    TrainingBlock,
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
            "sex": Profile.Sex.FEMALE,
            "date_of_birth": date(2002, 5, 4),
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
            "start_date": date(2026, 11, 1),
            "end_date": date(2027, 3, 1),
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
        return WorkoutSession.objects.create(**kwargs)

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


@pytest.fixture
def cycle(db, make_user, make_block, make_day):
    user = make_user()
    training_block = make_block(user=user, is_active=True)
    day1 = make_day(training_block=training_block, position=1)
    day2 = make_day(training_block=training_block, position=2)
    day3 = make_day(training_block=training_block, position=3)

    return {
        "user": user,
        "training_block": training_block,
        "day1": day1,
        "day2": day2,
        "day3": day3,
    }


@pytest.fixture
def make_finished_session(make_session):
    def _create_finished_session(*, user, planned_day, days_ago):
        now = timezone.now()
        started_at = now - timedelta(days=days_ago)
        finished_at = started_at + timedelta(hours=1)

        return make_session(
            user=user,
            planned_day=planned_day,
            started_at=started_at,
            finished_at=finished_at,
        )

    return _create_finished_session


@pytest.fixture
def other_user(db, make_user, make_block, make_day):
    user = make_user()
    training_block = make_block(user=user, is_active=True)
    day = make_day(training_block=training_block)

    return {"user": user, "training_block": training_block, "day": day}


@pytest.fixture
def day_with_unordered_exercises(
    db, make_user, make_block, make_day, make_planned_exercise
):
    user = make_user()
    training_block = make_block(user=user, is_active=True)
    day = make_day(training_block=training_block, position=1)
    exercise3 = make_planned_exercise(planned_day=day, position=3)
    exercise1 = make_planned_exercise(planned_day=day, position=1)
    exercise2 = make_planned_exercise(planned_day=day, position=2)

    return {
        "user": user,
        "training_block": training_block,
        "planned_day": day,
        "exercise3": exercise3,
        "exercise1": exercise1,
        "exercise2": exercise2,
    }


@pytest.fixture
def logged_in_cycle(client, cycle, make_profile):
    make_profile(user=cycle["user"])
    client.force_login(cycle["user"])

    return cycle


@pytest.fixture
def plan_session(cycle, make_session, make_planned_exercise, make_exercise):
    user = cycle["user"]
    session = make_session(user=user, planned_day=cycle["day1"])
    pe_day1 = make_planned_exercise(planned_day=cycle["day1"])
    pe_day2 = make_planned_exercise(planned_day=cycle["day2"])
    exercise_alt = make_exercise(name="Bulgarian Split Squat")

    return {
        "user": user,
        "session": session,
        "pe_day1": pe_day1,
        "pe_day2": pe_day2,
        "exercise_alt": exercise_alt,
    }
