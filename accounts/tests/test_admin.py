import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import NON_FIELD_ERRORS
from django.urls import reverse
from pytest_django.asserts import assertContains

User = get_user_model()


def user_form_data(**kwargs):
    data = {
        "username": "John",
        "email": "j.smith@example.com",
        "password1": "11}2IXJT?^mM4[Nk6`ml",
        "password2": "11}2IXJT?^mM4[Nk6`ml",
        "usable_password": "true",
    }
    data.update(kwargs)
    return data


def test_form_has_email(admin_client):
    url = reverse("admin:accounts_user_add")
    response = admin_client.get(url)

    assertContains(response, 'name="email"')


def test_form_creates_user_with_hashed_password(admin_client):
    url = reverse("admin:accounts_user_add")
    data = user_form_data()

    response = admin_client.post(url, data)

    assert response.status_code == 302
    user = User.objects.get(username=data["username"])
    assert response.url == reverse("admin:accounts_user_change", args=[user.pk])
    assert user.password != data["password1"]
    assert user.check_password(data["password1"])


@pytest.mark.parametrize(
    "email, error_key",
    [
        ("TEST@EXAMPLE.COM", NON_FIELD_ERRORS),
        ("", "email"),
    ],
    ids=["duplicate_uppercase", "empty"],
)
def test_form_rejects_invalid_email(admin_client, make_user, email, error_key):
    make_user(email="test@example.com")
    url = reverse("admin:accounts_user_add")
    data = user_form_data(email=email)
    users_before = User.objects.count()

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert User.objects.count() == users_before
    errors = response.context["adminform"].form.errors
    assert error_key in errors
