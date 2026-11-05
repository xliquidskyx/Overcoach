from django.contrib.auth.models import UserManager


class EmailRequiredUserManager(UserManager):
    def _validate_email(self, email: str | None) -> None:
        if not email or not email.strip():
            raise ValueError("Users must have an e-mail address.")

    def create_user(self, username, email=None, password=None, **extra_fields):
        self._validate_email(email)
        return super().create_user(username, email.strip(), password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        self._validate_email(email)
        return super().create_superuser(
            username, email.strip(), password, **extra_fields
        )
