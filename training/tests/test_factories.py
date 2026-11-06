import pytest

from django.contrib.auth import get_user_model

from training.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_make_user_create_distinct_objects(make_user):
    first_user = make_user()
    second_user = make_user()

    assert first_user.pk != second_user.pk
    assert User.objects.count() == 2


@pytest.mark.django_db
def test_make_profile_builds_its_own_user(make_profile):
    make_profile()
    make_profile()

    assert Profile.objects.count() == 2
    assert User.objects.count() == 2
