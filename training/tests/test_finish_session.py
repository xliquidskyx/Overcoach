from decimal import Decimal

import pytest

from training.exceptions import FinishSessionError
from training.services import finish_session, log_set, next_planned_day, start_session


def test_session_with_set_is_finished(plan_session, make_set_log):
    user = plan_session["user"]
    session = plan_session["session"]
    make_set_log(session=session)

    result, created = finish_session(user, session)

    assert created is True
    assert result.finished_at is not None
    assert result.finished_at >= result.started_at


def test_finishing_session_moves_cycle_to_next_day(cycle, make_exercise):
    user = cycle["user"]
    exercise = make_exercise()

    session, _ = start_session(user)
    log_set(user, session, exercise=exercise, weight=Decimal("80.0"), reps=8)
    finish_session(user, session)

    assert session.planned_day == cycle["day1"]
    assert next_planned_day(user) == cycle["day2"]


def test_finishing_finished_session_is_noop(plan_session, make_set_log):
    user = plan_session["user"]
    session = plan_session["session"]
    make_set_log(session=session)
    finish_session(user, session)
    first_finished_at = session.finished_at

    result, created = finish_session(user, session)

    assert created is False
    result.refresh_from_db()
    assert result.finished_at == first_finished_at


def test_session_without_sets_cannot_be_finished(plan_session):
    session = plan_session["session"]

    with pytest.raises(FinishSessionError, match="no sets"):
        finish_session(plan_session["user"], session)

    session.refresh_from_db()
    assert session.finished_at is None


def test_session_of_another_user_cannot_be_finished(
    plan_session, other_user, make_set_log
):
    session = plan_session["session"]
    make_set_log(session=session)

    with pytest.raises(FinishSessionError, match="does not belong"):
        finish_session(other_user["user"], session)

    session.refresh_from_db()
    assert session.finished_at is None
