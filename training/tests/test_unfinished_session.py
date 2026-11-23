from training.services import unfinished_session


def test_returns_unfinished_off_plan_session(make_user, make_session):
    user = make_user()
    session = make_session(user=user)

    result = unfinished_session(user)

    assert result == session


def test_returns_none_when_all_sessions_finished(make_user, make_finished_session):
    user = make_user()
    make_finished_session(user=user, planned_day=None, days_ago=1)

    assert unfinished_session(user=user) is None


def test_ignores_other_users_unfinished_session(make_user, make_session):
    user = make_user()
    other = make_user()
    make_session(user=other)

    assert unfinished_session(user=user) is None


def test_returns_unfinished_planned_session(cycle, make_session):
    session = make_session(user=cycle["user"], planned_day=cycle["day1"])

    result = unfinished_session(user=cycle["user"])

    assert result == session
