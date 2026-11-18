from training.services import next_planned_day


def test_returns_none_without_active_block(
    make_user, make_block, make_day, finished_session
):
    user = make_user()
    block = make_block(user=user, is_active=False)
    day = make_day(training_block=block)
    finished_session(user=user, planned_day=day, days_ago=1)

    result = next_planned_day(user)

    assert result is None


def test_returns_first_day_without_session(cycle):
    result = next_planned_day(cycle["user"])

    assert result == cycle["day1"]


def test_returns_none_without_days(make_user, make_block):
    user = make_user()
    make_block(user=user, is_active=True)

    result = next_planned_day(user)

    assert result is None


def test_returns_next_day_after_session(cycle, finished_session):
    finished_session(user=cycle["user"], planned_day=cycle["day1"], days_ago=1)

    result = next_planned_day(user=cycle["user"])

    assert result == cycle["day2"]


def test_end_of_cycle_returns_first_day(cycle, finished_session):
    finished_session(user=cycle["user"], planned_day=cycle["day3"], days_ago=1)

    result = next_planned_day(cycle["user"])

    assert result == cycle["day1"]


def test_skips_gap_in_positions(make_user, make_block, make_day, finished_session):
    user = make_user()
    block = make_block(user=user, is_active=True)
    day1 = make_day(training_block=block, position=1)
    day3 = make_day(training_block=block, position=3)
    make_day(training_block=block, position=4)
    finished_session(user=user, planned_day=day1, days_ago=1)

    result = next_planned_day(user)

    assert result == day3


def test_ignores_off_plan_session(cycle, finished_session):
    finished_session(user=cycle["user"], planned_day=cycle["day1"], days_ago=2)
    finished_session(user=cycle["user"], planned_day=None, days_ago=1)

    result = next_planned_day(cycle["user"])

    assert result == cycle["day2"]


def test_returns_day_of_unfinished_session(cycle, finished_session, make_session):
    finished_session(user=cycle["user"], planned_day=cycle["day1"], days_ago=1)
    make_session(user=cycle["user"], planned_day=cycle["day2"])

    result = next_planned_day(cycle["user"])

    assert result == cycle["day2"]


def test_other_users_sessions_do_not_affect_cycle(cycle, make_user, finished_session):
    finished_session(user=cycle["user"], planned_day=cycle["day1"], days_ago=2)
    user2 = make_user()
    finished_session(user=user2, planned_day=cycle["day2"], days_ago=1)

    result = next_planned_day(cycle["user"])

    assert result == cycle["day2"]
