from decimal import Decimal

import pytest
from django.db import IntegrityError

from training.exceptions import SetLogError
from training.models import SetLog
from training.services import log_set


@pytest.fixture
def off_plan(other_user, make_session, make_planned_exercise):
    user = other_user["user"]
    session = make_session(user=user, planned_day=None)
    pe = make_planned_exercise(planned_day=other_user["day"])
    return {"user": user, "session": session, "pe": pe}


def test_valid_set_creates_object(plan_session):
    pe_day1 = plan_session["pe_day1"]
    set_log, created = log_set(
        user=plan_session["user"],
        session=plan_session["session"],
        exercise=pe_day1.exercise,
        planned_exercise=pe_day1,
        weight=Decimal("80.0"),
        reps=8,
    )

    assert created is True
    assert set_log.set_number == 1
    assert SetLog.objects.filter(session=plan_session["session"]).count() == 1
    assert set_log.session == plan_session["session"]
    assert set_log.exercise == pe_day1.exercise
    assert set_log.planned_exercise == pe_day1
    assert set_log.weight == Decimal("80.0")
    assert set_log.reps == 8


def test_exercise_can_differ_from_planned_exercise(plan_session):
    set_log, created = log_set(
        user=plan_session["user"],
        session=plan_session["session"],
        exercise=plan_session["exercise_alt"],
        planned_exercise=plan_session["pe_day1"],
        weight=Decimal("80.0"),
        reps=8,
    )

    assert created is True
    assert set_log.exercise == plan_session["exercise_alt"]
    assert set_log.planned_exercise == plan_session["pe_day1"]


def test_second_set_exercise_has_number_two(plan_session):
    pe_day1 = plan_session["pe_day1"]
    params = dict(
        user=plan_session["user"],
        session=plan_session["session"],
        exercise=pe_day1.exercise,
        planned_exercise=pe_day1,
        weight=Decimal("80.0"),
        reps=8,
    )

    first, _ = log_set(**params)
    second, created = log_set(**params)

    assert created is True
    assert first.set_number == 1
    assert second.set_number == 2
    assert SetLog.objects.filter(session=plan_session["session"]).count() == 2


def test_next_set_number_follows_highest_not_count(plan_session, make_set_log):
    session = plan_session["session"]
    exercise = plan_session["pe_day1"].exercise
    make_set_log(session=session, exercise=exercise, set_number=1)
    make_set_log(session=session, exercise=exercise, set_number=3)

    set_log, created = log_set(
        user=plan_session["user"],
        session=session,
        exercise=exercise,
        weight=Decimal("80.0"),
        reps=8,
    )

    assert created is True
    assert set_log.set_number == 4
    assert SetLog.objects.filter(session=session, exercise=exercise).count() == 3


def test_set_number_is_counted_per_exercise(plan_session):
    pe_day1 = plan_session["pe_day1"]
    common = dict(
        user=plan_session["user"],
        session=plan_session["session"],
        planned_exercise=pe_day1,
        weight=Decimal("80.0"),
        reps=8,
    )
    log_set(exercise=pe_day1.exercise, **common)

    alt_set, created = log_set(exercise=plan_session["exercise_alt"], **common)

    assert created is True
    assert alt_set.set_number == 1
    assert SetLog.objects.filter(session=plan_session["session"]).count() == 2


def test_planned_exercise_from_other_day_is_rejected(plan_session):
    session = plan_session["session"]
    pe_day2 = plan_session["pe_day2"]

    with pytest.raises(SetLogError, match="planned day"):
        log_set(
            user=plan_session["user"],
            session=session,
            exercise=pe_day2.exercise,
            planned_exercise=pe_day2,
            weight=Decimal("80.0"),
            reps=8,
        )

    assert SetLog.objects.filter(session=session).count() == 0


def test_session_of_another_user_is_rejected(plan_session, other_user):
    session = plan_session["session"]
    pe_day1 = plan_session["pe_day1"]

    with pytest.raises(SetLogError, match="session does not belong"):
        log_set(
            user=other_user["user"],
            session=session,
            exercise=pe_day1.exercise,
            planned_exercise=pe_day1,
            weight=Decimal("80.0"),
            reps=8,
        )

    assert SetLog.objects.filter(session=session).count() == 0


def test_set_can_be_logged_to_finished_session(plan_session, make_finished_session):
    user = plan_session["user"]
    pe_day1 = plan_session["pe_day1"]
    finished = make_finished_session(
        user=user, planned_day=pe_day1.planned_day, days_ago=1
    )
    finished_at_before = finished.finished_at

    set_log, created = log_set(
        user=user,
        session=finished,
        exercise=pe_day1.exercise,
        planned_exercise=pe_day1,
        weight=Decimal("80.0"),
        reps=8,
    )

    assert created is True
    assert set_log.session == finished
    assert SetLog.objects.filter(session=finished).count() == 1

    finished.refresh_from_db()
    assert finished.finished_at == finished_at_before


def test_off_plan_session_rejects_planned_exercise(off_plan):
    session = off_plan["session"]

    with pytest.raises(SetLogError, match="planned day"):
        log_set(
            user=off_plan["user"],
            session=session,
            exercise=off_plan["pe"].exercise,
            planned_exercise=off_plan["pe"],
            weight=Decimal("80.0"),
            reps=8,
        )

    assert SetLog.objects.filter(session=session).count() == 0


def test_off_plan_session_accepts_set_without_planned_exercise(off_plan):
    set_log, created = log_set(
        user=off_plan["user"],
        session=off_plan["session"],
        exercise=off_plan["pe"].exercise,
        weight=Decimal("80.0"),
        reps=8,
    )

    assert created is True
    assert set_log.planned_exercise is None
    assert set_log.set_number == 1


def test_race_returns_existing_set(plan_session, make_set_log, monkeypatch):
    session = plan_session["session"]
    pe_day1 = plan_session["pe_day1"]
    existing = make_set_log(
        session=session,
        exercise=pe_day1.exercise,
        planned_exercise=pe_day1,
        set_number=1,
        weight=Decimal("80.0"),
    )
    monkeypatch.setattr(
        "training.services._next_set_number", lambda session, exercise: 1
    )

    result, created = log_set(
        user=plan_session["user"],
        session=session,
        exercise=pe_day1.exercise,
        planned_exercise=pe_day1,
        weight=Decimal("90.0"),
        reps=8,
    )

    assert created is False
    assert result == existing
    assert result.weight == Decimal("80.0")
    assert SetLog.objects.filter(session=session).count() == 1


def test_other_integrity_errors_are_not_swallowed(plan_session):
    pe_day1 = plan_session["pe_day1"]

    with pytest.raises(IntegrityError):
        log_set(
            user=plan_session["user"],
            session=plan_session["session"],
            exercise=pe_day1.exercise,
            planned_exercise=pe_day1,
            weight=Decimal("80.0"),
            reps=0,
        )
