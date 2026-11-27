from datetime import date, timedelta

import pytest
from django.utils import timezone

from training.forms import MAX_AGE, MAX_HEIGHT, MIN_AGE, MIN_HEIGHT, ProfileForm

FIXED_TODAY = date(2026, 11, 15)
TURNS_MIN_AGE_TODAY = FIXED_TODAY.replace(year=FIXED_TODAY.year - MIN_AGE)
TURNS_MIN_AGE_TOMORROW = TURNS_MIN_AGE_TODAY + timedelta(days=1)
TURNS_OVER_MAX_TODAY = FIXED_TODAY.replace(year=FIXED_TODAY.year - MAX_AGE - 1)
TURNS_OVER_MAX_TOMORROW = TURNS_OVER_MAX_TODAY + timedelta(days=1)


def profile_form_data(**kwargs):
    data = {
        "sex": "female",
        "date_of_birth": "1995-06-01",
        "goal": "hypertrophy",
        "level": 1,
    }
    data.update(kwargs)
    return data


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: FIXED_TODAY)
    return FIXED_TODAY


def test_valid_data_without_height():
    form = ProfileForm(data=profile_form_data())

    assert form.is_valid()
    assert form.cleaned_data["height_cm"] is None


@pytest.mark.parametrize("height", [MIN_HEIGHT, MAX_HEIGHT])
def test_height_on_range_ends_is_accepted(height):
    form = ProfileForm(data=profile_form_data(height_cm=height))

    assert form.is_valid()
    assert form.cleaned_data["height_cm"] == height


@pytest.mark.parametrize("height", [MIN_HEIGHT - 1, MAX_HEIGHT + 1, 0])
def test_height_out_of_range_is_rejected(height):
    form = ProfileForm(data=profile_form_data(height_cm=height))

    assert not form.is_valid()
    assert "height_cm" in form.errors


@pytest.mark.parametrize(
    "date_of_birth",
    [TURNS_MIN_AGE_TODAY, TURNS_OVER_MAX_TOMORROW],
    ids=["exactly_min_age", "exactly_max_age"],
)
def test_age_on_range_ends_is_accepted(date_of_birth):
    form = ProfileForm(data=profile_form_data(date_of_birth=date_of_birth.isoformat()))

    assert form.is_valid()
    assert form.cleaned_data["date_of_birth"] == date_of_birth


@pytest.mark.parametrize(
    "date_of_birth",
    [
        TURNS_MIN_AGE_TOMORROW,
        TURNS_OVER_MAX_TODAY,
        FIXED_TODAY,
        FIXED_TODAY + timedelta(days=1),
    ],
    ids=[
        "turns_min_age_tomorrow",
        "turns_over_max_today",
        "born_today",
        "born_tomorrow",
    ],
)
def test_age_out_of_range_is_rejected(date_of_birth):
    form = ProfileForm(data=profile_form_data(date_of_birth=date_of_birth.isoformat()))

    assert not form.is_valid()
    assert "date_of_birth" in form.errors


@pytest.mark.parametrize("sex", ["Female", "Male"])
def test_sex_not_in_choices_rejected(sex):
    form = ProfileForm(data=profile_form_data(sex=sex))

    assert not form.is_valid()
    assert "sex" in form.errors
