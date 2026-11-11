from django.db import models
from django.db.models import CheckConstraint, UniqueConstraint, Q, F
from django.conf import settings
from django.utils import timezone


class Exercise(models.Model):
    class Category(models.TextChoices):
        SQUAT = "squat", "Squat"
        HINGE = "hinge", "Hinge"
        LUNGE = "lunge", "Lunge / single-leg"
        HORIZONTAL_PUSH = "horizontal_push", "Horizontal push"
        VERTICAL_PUSH = "vertical_push", "Vertical push"
        HORIZONTAL_PULL = "horizontal_pull", "Horizontal pull"
        VERTICAL_PULL = "vertical_pull", "Vertical pull"
        CARRY = "carry", "Carry"
        CORE = "core", "Core"
        ISOLATION = "isolation", "Isolation"
        CONDITIONING = "conditioning", "Conditioning / cardio"
        MOBILITY = "mobility", "Mobility"

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(choices=Category, max_length=20)

    def __str__(self):
        return self.name


class Profile(models.Model):
    class Goal(models.TextChoices):
        HYPERTROPHY = "hypertrophy", "Muscle building"
        STRENGTH = "strength", "Strength"
        FAT_LOSS = "fat_loss", "Fat loss"
        RECOMPOSITION = "recomposition", "Body recomposition"
        GENERAL_FITNESS = "general_fitness", "General fitness"

    class Level(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    goal = models.CharField(choices=Goal, max_length=20)
    level = models.PositiveSmallIntegerField(choices=Level)
    excluded_exercises = models.ManyToManyField(
        Exercise, related_name="excluded_by", blank=True
    )
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class TrainingBlock(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks"
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="training_block_one_active_per_user",
            ),
            CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="training_block_end_date_after_start_date",
            ),
        ]
        ordering = ["-start_date", "-id"]

    @property
    def duration_days(self):
        """Length of the block in days, counting both the start and the end date."""
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return self.name


class PlannedDay(models.Model):
    training_block = models.ForeignKey(
        TrainingBlock, on_delete=models.CASCADE, related_name="days"
    )
    name = models.CharField(max_length=50)
    position = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["training_block", "position"],
                name="planned_day_position_must_be_unique",
            )
        ]
        ordering = ["position"]

    def __str__(self):
        return self.name


class PlannedExercise(models.Model):
    planned_day = models.ForeignKey(
        PlannedDay, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise = models.ForeignKey(
        Exercise, on_delete=models.PROTECT, related_name="planned_exercises"
    )
    position = models.PositiveSmallIntegerField()
    sets = models.PositiveSmallIntegerField()
    reps_min = models.PositiveSmallIntegerField()
    reps_max = models.PositiveSmallIntegerField()
    weight = models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True)
    rest_seconds = models.PositiveSmallIntegerField()
    rir = models.PositiveSmallIntegerField(blank=True, null=True)
    rpe = models.DecimalField(decimal_places=1, max_digits=3, blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["planned_day", "position"],
                name="planned_exercise_position_must_be_unique",
            ),
            CheckConstraint(
                condition=Q(reps_max__gte=F("reps_min")),
                name="planned_exercise_reps_max_gte_reps_min",
            ),
            CheckConstraint(
                condition=Q(rpe__range=(0, 10)),
                name="planned_exercise_rpe_between_0_and_10",
            ),
            CheckConstraint(condition=Q(sets__gt=0), name="planned_exercise_sets_gt_0"),
            CheckConstraint(
                condition=Q(reps_min__gt=0), name="planned_exercise_reps_min_gt_0"
            ),
            CheckConstraint(
                condition=Q(weight__range=(0, 1000)),
                name="planned_exercise_weight_between_0_and_1000",
            ),
            CheckConstraint(
                condition=Q(rir__lte=10), name="planned_exercise_rir_lte_10"
            ),
        ]
        ordering = ["position"]

    def __str__(self):
        return self.exercise.name


class WorkoutSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_sessions",
    )
    planned_day = models.ForeignKey(
        PlannedDay,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sessions",
    )
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(finished_at__gte=F("started_at")),
                name="workout_session_finished_at_after_started_at",
            )
        ]
        ordering = ["-started_at", "-id"]

    def __str__(self):
        started_at = timezone.localtime(self.started_at)
        if self.planned_day:
            return f"{started_at:%Y-%m-%d %H:%M} - {self.planned_day.name}"
        return f"{started_at:%Y-%m-%d %H:%M} - Off-plan workout"


class SetLog(models.Model):
    session = models.ForeignKey(
        WorkoutSession, on_delete=models.CASCADE, related_name="sets"
    )
    exercise = models.ForeignKey(
        Exercise, on_delete=models.PROTECT, related_name="set_logs"
    )
    planned_exercise = models.ForeignKey(
        PlannedExercise,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="set_logs",
    )
    set_number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    rir = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["session", "exercise", "set_number"],
                name="set_log_set_number_unique_per_session_exercise",
            ),
            CheckConstraint(
                condition=Q(set_number__gt=0), name="set_log_set_number_gt_0"
            ),
            CheckConstraint(condition=Q(reps__gt=0), name="set_log_reps_gt_0"),
            CheckConstraint(
                condition=Q(weight__range=(0, 1000)),
                name="set_log_weight_between_0_and_1000",
            ),
            CheckConstraint(condition=Q(rir__lte=10), name="set_log_rir_lte_10"),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.exercise} – set {self.set_number}"


class Measurement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="measurements"
    )
    date = models.DateField(default=timezone.localdate)
    body_weight = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    body_fat_percent = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    muscle_mass = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    calf = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    thigh = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    hips = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    belly = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    waist = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    under_bust = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    chest = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    arm = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "date"], name="measurement_one_per_user_per_day"
            ),
            CheckConstraint(
                condition=Q(body_fat_percent__range=(0, 100)),
                name="measurement_body_fat_percent_between_0_and_100",
            ),
            CheckConstraint(
                condition=Q(muscle_mass__gte=0), name="measurement_muscle_mass_gte_0"
            ),
            CheckConstraint(
                condition=Q(body_weight__isnull=False)
                | Q(body_fat_percent__isnull=False)
                | Q(muscle_mass__isnull=False)
                | Q(calf__isnull=False)
                | Q(thigh__isnull=False)
                | Q(hips__isnull=False)
                | Q(belly__isnull=False)
                | Q(waist__isnull=False)
                | Q(under_bust__isnull=False)
                | Q(chest__isnull=False)
                | Q(arm__isnull=False),
                name="measurement_at_least_one_field_not_null",
            ),
        ]
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.user.username} - {self.date} Measurement"
