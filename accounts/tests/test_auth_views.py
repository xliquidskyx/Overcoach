import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db
LOGIN_URL = reverse("accounts:login")
LOGOUT_URL = reverse("accounts:logout")
HOME_URL = reverse("training:home")
PASSWORD = "s8DXee93_29`~"


def test_login_with_valid_credentials_redirects_home(client, make_user):
    user = make_user(password=PASSWORD)
    response = client.post(LOGIN_URL, {"username": user.username, "password": PASSWORD})

    assertRedirects(response, HOME_URL, fetch_redirect_response=False)
    assert client.session["_auth_user_id"] == str(user.pk)


def test_login_with_invalid_password_shows_error(client, make_user):
    user = make_user(password=PASSWORD)
    response = client.post(
        LOGIN_URL, {"username": user.username, "password": "incorrect"}
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    assert response.context["form"].non_field_errors()


def test_unauthorized_user_redirects_to_login(client):
    response = client.get(HOME_URL)

    assertRedirects(
        response, f"{LOGIN_URL}?next={HOME_URL}", fetch_redirect_response=False
    )


def test_next_in_url_works_after_login(client, make_user):
    user = make_user(password=PASSWORD)
    response = client.post(
        f"{LOGIN_URL}?next=/trainings/onboarding/",
        {"username": user.username, "password": PASSWORD},
    )

    assertRedirects(
        response, reverse("training:onboarding"), fetch_redirect_response=False
    )


def test_next_to_an_unknown_website_is_ignored(client, make_user):
    user = make_user(password=PASSWORD)
    response = client.post(
        f"{LOGIN_URL}?next=https://evil.com/",
        {"username": user.username, "password": PASSWORD},
    )

    assertRedirects(response, HOME_URL, fetch_redirect_response=False)


def test_logged_in_user_redirected_from_login_to_home(client, make_user):
    client.force_login(make_user())
    response = client.get(LOGIN_URL)

    assertRedirects(response, HOME_URL, fetch_redirect_response=False)


def test_logout_redirects_to_login(client, make_user):
    client.force_login(make_user())
    response = client.post(LOGOUT_URL)

    assertRedirects(response, LOGIN_URL, fetch_redirect_response=False)
    assert not "_auth_user_id" in client.session


def test_get_logout_is_rejected_and_keeps_user_logged_in(client, make_user):
    client.force_login(make_user())
    response = client.get(LOGOUT_URL)

    assert response.status_code == 405
    assert "_auth_user_id" in client.session
