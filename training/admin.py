from django.contrib import admin
from django.db.models import Count

from .models import (
    Exercise,
    Measurement,
    PlannedDay,
    PlannedExercise,
    Profile,
    SetLog,
    TrainingBlock,
    WorkoutSession,
)


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


class SetLogInline(admin.TabularInline):
    model = SetLog
    fields = ["exercise", "planned_exercise", "set_number", "reps", "weight", "rir"]
    extra = 0
    autocomplete_fields = ["exercise"]
    raw_id_fields = ["planned_exercise"]


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    inlines = [SetLogInline]
    list_display = ["started_at", "user", "planned_day", "finished_at", "set_count"]
    list_filter = ["started_at"]
    date_hierarchy = "started_at"
    list_select_related = ["user", "planned_day"]
    raw_id_fields = ["planned_day"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(set_count=Count("sets"))

    @admin.display(description="Sets", ordering="set_count")
    def set_count(self, obj):
        return obj.set_count


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ["date", "user", "body_weight", "waist", "hips"]
    list_filter = ["date"]
    date_hierarchy = "date"
    list_select_related = ["user"]
    fieldsets = [
        (None, {"fields": ["user", "date"]}),
        (
            "Body composition",
            {"fields": ["body_weight", "body_fat_percent", "muscle_mass"]},
        ),
        (
            "Circumferences (cm)",
            {
                "fields": [
                    "calf",
                    "thigh",
                    "hips",
                    "belly",
                    "waist",
                    "under_bust",
                    "chest",
                    "arm",
                ]
            },
        ),
    ]
