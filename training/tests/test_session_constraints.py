import datetime
import pytest
from django.db import IntegrityError
from django.utils import timezone
from training.models import Measurement, SetLog, WorkoutSession


def test_two_measurements_per_user_per_day_raise_error(make_measurement):
    measurement = make_measurement(date=datetime.date(2026, 11, 12))
    with pytest.raises(IntegrityError):
        make_measurement(user=measurement.user, date=datetime.date(2026, 11, 12))


def test_two_measurements_for_two_users_creates_object(make_measurement):
    make_measurement(date=datetime.date(2026, 11, 12))
    make_measurement(date=datetime.date(2026, 11, 12))

    assert Measurement.objects.count() == 2


def test_body_fat_percent_at_range_values_creates_object(make_measurement):
    make_measurement(body_fat_percent=0)
    make_measurement(body_fat_percent=100)

    assert Measurement.objects.count() == 2


@pytest.mark.parametrize("body_fat_percent", [-1, 101])
def test_body_fat_percent_out_of_range_raises_error(make_measurement, body_fat_percent):
    with pytest.raises(IntegrityError):
        make_measurement(body_fat_percent=body_fat_percent)


def test_muscle_mass_gte_0_creates_object(make_measurement):
    make_measurement(muscle_mass=0)
    make_measurement(muscle_mass=40)

    assert Measurement.objects.count() == 2


def test_muscle_mass_lt_0_raises_error(make_measurement):
    with pytest.raises(IntegrityError):
        make_measurement(muscle_mass=-1)


def test_object_with_no_measurements_raises_error(make_measurement):
    with pytest.raises(IntegrityError):
        make_measurement(body_weight=None)


@pytest.mark.parametrize(
    "field, value",
    [
        ("muscle_mass", 30),
        ("body_fat_percent", 20),
        ("calf", 40),
        ("thigh", 55),
        ("hips", 100),
        ("belly", 66),
        ("waist", 60),
        ("under_bust", 70),
        ("chest", 80),
        ("arm", 35),
    ],
)
def test_at_least_one_measurement_creates_object(make_measurement, field, value):
    make_measurement(body_weight=None, **{field: value})


def test_session_finished_at_lt_started_at_raises_error(make_session):
    now = timezone.now()
    with pytest.raises(IntegrityError):
        make_session(started_at=now, finished_at=now - datetime.timedelta(minutes=1))


@pytest.mark.parametrize(
    "duration", [None, datetime.timedelta(0), datetime.timedelta(hours=1)]
)
def test_session_valid_finished_at_creates_object(make_session, duration):
    now = timezone.now()
    finished_at = None if duration is None else now + duration
    make_session(started_at=now, finished_at=finished_at)


def test_two_duplicate_set_numbers_raise_error(make_set_log):
    set_log = make_set_log(set_number=1)
    with pytest.raises(IntegrityError):
        make_set_log(session=set_log.session, exercise=set_log.exercise, set_number=1)


def test_set_number_lte_0_raises_error(make_set_log):
    with pytest.raises(IntegrityError):
        make_set_log(set_number=0)


def test_set_reps_lte_0_raises_error(make_set_log):
    with pytest.raises(IntegrityError):
        make_set_log(reps=0)


def test_set_weight_at_range_ends_creates_object(make_set_log):
    make_set_log(weight=0)
    make_set_log(weight=1000)

    assert SetLog.objects.count() == 2


@pytest.mark.parametrize("weight", [-1, 1001])
def test_set_weight_out_of_range_raises_error(make_set_log, weight):
    with pytest.raises(IntegrityError):
        make_set_log(weight=weight)


def test_set_rir_at_range_end_creates_object(make_set_log):
    make_set_log(rir=0)
    make_set_log(rir=10)

    assert SetLog.objects.count() == 2


@pytest.mark.parametrize("rir", [-1, 11])
def test_set_rir_out_of_range_raises_error(make_set_log, rir):
    with pytest.raises(IntegrityError):
        make_set_log(rir=rir)
