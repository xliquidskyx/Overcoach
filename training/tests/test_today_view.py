import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains

pytestmark = pytest.mark.django_db
TODAY_URL = reverse("training:today")


def test_profile_without_block_shows_empty_state(client, make_user, make_profile):
    user = make_user()
    make_profile(user=user)
    client.force_login(user=user)

    response = client.get(TODAY_URL)

    assert response.context["day"] is None
    assert response.context["session"] is None
    assertContains(response, "You have no active plan")


def test_active_cycle_returns_first_day(client, logged_in_cycle):
    response = client.get(TODAY_URL)

    assert response.context["day"] == logged_in_cycle["day1"]
    assertContains(response, logged_in_cycle["day1"].name)
    assert response.context["session"] is None


def test_exercises_sorted_by_position(
    client, day_with_unordered_exercises, make_profile
):
    user = day_with_unordered_exercises["user"]
    exercise1 = day_with_unordered_exercises["exercise1"]
    exercise2 = day_with_unordered_exercises["exercise2"]
    exercise3 = day_with_unordered_exercises["exercise3"]
    make_profile(user=user)
    client.force_login(user=user)

    response = client.get(TODAY_URL)

    assert list(response.context["day"].exercises.all()) == [
        exercise1,
        exercise2,
        exercise3,
    ]


def test_active_off_plan_session_blocks_next_planned_day(
    client, logged_in_cycle, make_session
):
    user = logged_in_cycle["user"]
    session = make_session(user=user)

    response = client.get(TODAY_URL)

    assert response.context["session"] == session
    assert response.context["day"] is None
    assertContains(response, "In progress")


def test_returns_unfinished_planned_session(client, logged_in_cycle, make_session):
    user = logged_in_cycle["user"]
    day = logged_in_cycle["day2"]
    make_session(user=user, planned_day=day)

    response = client.get(TODAY_URL)

    assert response.context["session"].planned_day == day
    assert response.context["day"] is None
    assertContains(response, day.name)
