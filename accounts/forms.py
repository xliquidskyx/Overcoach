from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self) -> str:
        cleaned_email = self.cleaned_data["email"].strip()

        if User.objects.filter(email__iexact=cleaned_email).exists():
            raise ValidationError("Account with this e-mail already exists.")

        return cleaned_email
