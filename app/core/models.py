"""
Database Models.
"""

import os
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings


def recipe_image_file_path(instance, filename):
    """Generate file path for new recipe image."""
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    return os.path.join('uploads', 'recipe', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, Save, and Return User."""
        if not email:
            raise ValueError('User Must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create, Save, and Return Super User."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User Table in the System."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # User.objects => User Manager.
    objects = UserManager()
    # Use Email for login istead of name(default in django).
    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Recipe Table in the System."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    tags = models.ManyToManyField('Tag')
    ingrediants = models.ManyToManyField('Ingrediant')
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self) -> str:
        return self.title


class Tag(models.Model):
    """Tag table in the system."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Ingrediant(models.Model):
    """Ingrediant Table in the System."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
