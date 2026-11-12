import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user(make_user):
    user = make_user(username="Laura", email="laura@example.com")
    user.refresh_from_db()
    assert user.username == "Laura"
    assert user.password != "strongpassword"  # Checks if pwd has been hashed
    assert user.check_password("strongpassword")
    assert user.email == "laura@example.com"


@pytest.mark.django_db
def test_create_user_without_email_raises_error(make_user):
    with pytest.raises(ValueError):
        make_user(email=None)


@pytest.mark.django_db
def test_create_user_with_empty_email_raises_error(make_user):
    with pytest.raises(ValueError):
        make_user(email=" ")


@pytest.mark.django_db
def test_create_superuser(make_user):
    user = User.objects.create_superuser(
        username="Laura", email="laura@example.com", password="strongpassword"
    )
    user.refresh_from_db()
    assert user.username == "Laura"
    assert user.password != "strongpassword"  # Checks if pwd has been hashed
    assert user.check_password("strongpassword")
    assert user.email == "laura@example.com"
    assert user.is_staff
    assert user.is_superuser


@pytest.mark.django_db
def test_create_superuser_without_email_raises_error():
    with pytest.raises(ValueError):
        User.objects.create_superuser(username="John", password="strongpassword")
