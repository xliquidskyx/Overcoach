from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import EmailRequiredUserManager


class User(AbstractUser):
    email = models.EmailField("email address", blank=False, unique=True)

    objects = EmailRequiredUserManager()

    def __str__(self):
        return self.username
