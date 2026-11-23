import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db
REGISTER_URL = reverse("accounts:register")
User = get_user_model()


def register_form_data(**kwargs):
    data = {
        "username": "John",
        "email": "j.smith@example.com",
        "password1": "8DXee93_29`~",
        "password2": "8DXee93_29`~",
    }
    data.update(kwargs)
    return data


def test_register_creates_user_and_logs_in(client):
    response = client.post(REGISTER_URL, register_form_data())

    user = User.objects.get(username="John")
    assert user.email == "j.smith@example.com"
    assertRedirects(response, reverse("training:today"), fetch_redirect_response=False)
    assert client.session["_auth_user_id"] == str(user.pk)


def test_get_register_shows_form(client):
    response = client.get(REGISTER_URL)

    assert response.status_code == 200
    assert "email" in response.context["form"].fields


@pytest.mark.parametrize(
    "email",
    [
        "taken@example.com",
        "TAKEN@EXAMPLE.COM",
        "Taken@Example.com",
        " taken@example.com ",
    ],
    ids=["exact", "upper", "mixed", "spaces"],
)
def test_register_does_not_accept_duplicate_emails(client, email, make_user):
    make_user(email="taken@example.com")
    response = client.post(REGISTER_URL, register_form_data(email=email))

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert User.objects.count() == 1
    assert "_auth_user_id" not in client.session


def test_register_different_passwords_do_not_create_account(client):
    response = client.post(REGISTER_URL, register_form_data(password2="J40C;y7x{Jt£"))

    assert response.status_code == 200
    assert "password2" in response.context["form"].errors
    assert not User.objects.filter(username="John").exists()


def test_register_blank_email_does_not_create_account(client):
    response = client.post(REGISTER_URL, register_form_data(email=""))

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert not User.objects.filter(username="John").exists()


def test_logged_in_user_does_not_see_register_form(client, make_user):
    client.force_login(make_user())
    response = client.get(REGISTER_URL)

    assertRedirects(response, reverse("training:today"), fetch_redirect_response=False)


def test_logged_in_user_cannot_send_register_form(client, make_user):
    client.force_login(make_user())
    response = client.post(REGISTER_URL, register_form_data())

    assert User.objects.count() == 1
    assertRedirects(response, reverse("training:today"), fetch_redirect_response=False)
