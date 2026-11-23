from training.services import days_with_exercises


def test_only_returns_days_of_the_user(cycle, other_user):
    result = list(days_with_exercises(cycle["user"]))

    assert result == [cycle["day1"], cycle["day2"], cycle["day3"]]


def test_exercises_sorted_by_position(day_with_unordered_exercises):
    user = day_with_unordered_exercises["user"]
    planned_day = day_with_unordered_exercises["planned_day"]

    day = days_with_exercises(user).get(pk=planned_day.pk)
    result = list(day.exercises.all())

    assert result == [
        day_with_unordered_exercises["exercise1"],
        day_with_unordered_exercises["exercise2"],
        day_with_unordered_exercises["exercise3"],
    ]
