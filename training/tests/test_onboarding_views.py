import pytest
from datetime import date
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed
from training.models import Profile

HOME_URL = reverse("training:today")
ONBOARDING_URL = reverse("training:onboarding")
LOGIN_URL = reverse("accounts:login")

pytestmark = pytest.mark.django_db


def profile_form_data(**kwargs):
    data = {
        "sex": "female",
        "date_of_birth": "1995-06-01",
        "goal": "hypertrophy",
        "level": 1,
    }
    data.update(kwargs)
    return data


def test_onboarding_post_creates_profile_and_redirects_home(client, make_user):
    user = make_user()
    client.force_login(user)
    response = client.post(ONBOARDING_URL, profile_form_data(height_cm=168))

    assertRedirects(response, HOME_URL)
    profile = Profile.objects.get(user=user)
    assert profile.sex == "female"
    assert profile.date_of_birth == date(1995, 6, 1)
    assert profile.height_cm == 168
    assert profile.excluded_exercises.count() == 0


def test_home_without_profile_redirects_onboarding(client, make_user):
    client.force_login(make_user())
    response = client.get(HOME_URL)

    assertRedirects(response, ONBOARDING_URL)


def test_home_with_profile_returns_status_200(client, make_user, make_profile):
    user = make_user()
    client.force_login(user)
    make_profile(user=user)
    response = client.get(HOME_URL)

    assert response.status_code == 200
    assertTemplateUsed(response, "training/today.html")


def test_onboarding_without_profile_returns_form(client, make_user):
    client.force_login(make_user())
    response = client.get(ONBOARDING_URL)

    assert response.status_code == 200
    form = response.context["form"]
    assert set(form.fields) == {"sex", "date_of_birth", "height_cm", "goal", "level"}


def test_onboarding_with_profile_redirects_home(client, make_user, make_profile):
    user = make_user()
    client.force_login(user)
    make_profile(user=user)
    response = client.get(ONBOARDING_URL)

    assertRedirects(response, HOME_URL)


def test_onboarding_with_unauthorized_redirects_login(client):
    response = client.get(ONBOARDING_URL)

    assertRedirects(
        response, f"{LOGIN_URL}?next={ONBOARDING_URL}", fetch_redirect_response=False
    )


def test_onboarding_post_with_invalid_data_shows_error(client, make_user):
    user = make_user()
    client.force_login(user)
    response = client.post(ONBOARDING_URL, profile_form_data(height_cm=300))

    assert response.status_code == 200
    assert "height_cm" in response.context["form"].errors
    assert not Profile.objects.filter(user=user).exists()


def test_onboarding_duplicate_profile_does_not_replace_old_data(
    client, make_user, make_profile
):
    user = make_user()
    client.force_login(user)
    profile = make_profile(user=user, goal=Profile.Goal.HYPERTROPHY)
    response = client.post(
        ONBOARDING_URL, profile_form_data(goal=Profile.Goal.STRENGTH)
    )

    assertRedirects(response, HOME_URL)
    assert Profile.objects.filter(user=user).count() == 1
    profile.refresh_from_db()
    assert profile.goal == Profile.Goal.HYPERTROPHY
