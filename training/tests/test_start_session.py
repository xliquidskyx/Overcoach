from training.models import WorkoutSession
from training.services import start_session


def test_creates_session_for_first_day_when_no_sessions(cycle):
    user = cycle["user"]

    session, created = start_session(user)

    assert created is True
    assert session.planned_day == cycle["day1"]
    assert session.finished_at is None
    assert session.user == user
    assert WorkoutSession.objects.filter(user=user).count() == 1


def test_creates_session_for_next_day_after_finished_session(
    cycle, make_finished_session
):
    make_finished_session(user=cycle["user"], planned_day=cycle["day1"], days_ago=1)

    session, created = start_session(cycle["user"])

    assert session.planned_day == cycle["day2"]
    assert created is True


def test_returns_existing_unfinished_session(cycle, make_session):
    existing = make_session(user=cycle["user"], planned_day=cycle["day1"])

    session, created = start_session(cycle["user"])

    assert session == existing
    assert created is False
    assert WorkoutSession.objects.filter(user=cycle["user"]).count() == 1


def test_returns_unfinished_off_plan_session_even_with_active_block(
    cycle, make_session
):
    existing = make_session(user=cycle["user"])  # Off-plan session

    session, created = start_session(cycle["user"])

    assert session == existing
    assert created is False
    assert WorkoutSession.objects.filter(user=cycle["user"]).count() == 1


def test_other_users_unfinished_session_does_not_block(cycle, other_user, make_session):
    make_session(user=other_user["user"])

    session, created = start_session(cycle["user"])

    assert session.planned_day == cycle["day1"]
    assert session.user == cycle["user"]
    assert created is True
    assert WorkoutSession.objects.filter(
        user=other_user["user"], finished_at__isnull=True
    ).exists()


def test_creates_off_plan_session_without_active_block(make_user):
    user = make_user()

    session, created = start_session(user)

    assert session.planned_day is None
    assert created is True


def test_returns_unfinished_off_plan_session_without_active_block(
    make_user, make_session
):
    user = make_user()
    existing = make_session(user=user)

    session, created = start_session(user)

    assert session == existing
    assert session.planned_day is None
    assert created is False
    assert WorkoutSession.objects.filter(user=user).count() == 1


def test_returns_existing_session_when_insert_hits_unique_constraint(
    monkeypatch, make_user, make_session
):
    user = make_user()
    existing = make_session(user=user)
    monkeypatch.setattr("training.services.unfinished_session", lambda user: None)

    session, created = start_session(user)

    assert session == existing
    assert created is False
    assert WorkoutSession.objects.filter(user=user).count() == 1
