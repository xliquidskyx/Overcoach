import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db
LOGIN_URL = reverse("accounts:login")


def day_detail_url(day):
    return reverse("training:day_detail", args=[day.pk])


def test_day_detail_anonymous_user_redirects_to_login(client, cycle):
    url = day_detail_url(cycle["day1"])

    response = client.get(url)

    assertRedirects(response, f"{LOGIN_URL}?next={url}", fetch_redirect_response=False)


def test_user_day_detail_returns_200(client, logged_in_cycle):
    url = day_detail_url(logged_in_cycle["day1"])

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["day"] == logged_in_cycle["day1"]
    assertContains(response, logged_in_cycle["day1"].name)


def test_other_user_day_detail_returns_404(client, logged_in_cycle, other_user):
    url = day_detail_url(other_user["day"])

    response = client.get(url)

    assert response.status_code == 404


def test_day_from_inactive_block_returns_200(
    client, logged_in_cycle, make_block, make_day
):
    block = make_block(user=logged_in_cycle["user"], is_active=False)
    day = make_day(training_block=block)
    url = day_detail_url(day)

    response = client.get(url)

    assert response.status_code == 200
