from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.db.models.functions import Lower

from .managers import EmailRequiredUserManager


class User(AbstractUser):
    email = models.EmailField("email address")
    objects = EmailRequiredUserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            UniqueConstraint(
                Lower("email"),
                name="user_email_ci_unique",
                violation_error_message="A user with that email already exists.",
            ),
            CheckConstraint(condition=~Q(email=""), name="user_email_not_empty"),
        ]

    def __str__(self):
        return self.username
