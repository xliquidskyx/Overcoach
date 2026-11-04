from django.db import models
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
    excluded_exercises = models.ManyToManyField(Exercise, related_name="excluded_by", blank=True)

    def __str__(self):
        return self.user.username