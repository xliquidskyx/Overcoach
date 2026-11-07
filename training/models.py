from django.db import models
from django.db.models import CheckConstraint, UniqueConstraint, Q, F
from django.conf import settings


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
    category = models.CharField(choices=Category, max_length=15)

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
    goal = models.CharField(choices=Goal, max_length=15)
    level = models.PositiveSmallIntegerField(choices=Level)
    excluded_exercises = models.ManyToManyField(
        Exercise, related_name="excluded_by", blank=True
    )

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
        ]
        ordering = ["position"]

    def __str__(self):
        return self.exercise.name
