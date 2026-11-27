from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Profile

MIN_HEIGHT = 50
MAX_HEIGHT = 280
MIN_AGE = 16
MAX_AGE = 110


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("sex", "date_of_birth", "height_cm", "goal", "level")
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "height_cm": forms.NumberInput(
                attrs={"min": MIN_HEIGHT, "max": MAX_HEIGHT}
            ),
        }

    def clean_date_of_birth(self):
        today = timezone.localdate()
        date_of_birth = self.cleaned_data["date_of_birth"]

        if date_of_birth > today:
            raise ValidationError("Date of birth cannot be in the future.")

        age = (
            today.year
            - date_of_birth.year
            - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        )
        if age < MIN_AGE:
            raise ValidationError(f"User must be at least {MIN_AGE} years old.")
        elif age > MAX_AGE:
            raise ValidationError(f"User must be at most {MAX_AGE} years old.")

        return date_of_birth

    def clean_height_cm(self):
        height = self.cleaned_data["height_cm"]

        if height is None:
            return height

        if height < MIN_HEIGHT or height > MAX_HEIGHT:
            raise ValidationError(
                f"Height must be between {MIN_HEIGHT} and {MAX_HEIGHT} cm."
            )

        return height
