from django.contrib import admin
from .models import Exercise, PlannedDay, PlannedExercise, Profile, TrainingBlock


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    search_fields = ["name"]
    list_filter = ["category"]
    ordering = ["name"]


class PlannedDayInline(admin.TabularInline):
    model = PlannedDay
    extra = 0
    show_change_link = True


@admin.register(TrainingBlock)
class TrainingBlockAdmin(admin.ModelAdmin):
    inlines = [PlannedDayInline]
    list_display = [
        "name",
        "user",
        "start_date",
        "end_date",
        "is_active",
        "duration_days",
    ]
    list_filter = ["is_active"]
    list_select_related = ["user"]


class PlannedExerciseInline(admin.TabularInline):
    model = PlannedExercise
    extra = 0
    autocomplete_fields = ["exercise"]


@admin.register(PlannedDay)
class PlannedDayAdmin(admin.ModelAdmin):
    inlines = [PlannedExerciseInline]
    list_display = ["name", "training_block", "position"]
    list_select_related = ["training_block"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "goal", "level"]
    list_select_related = ["user"]
    autocomplete_fields = ["excluded_exercises"]
