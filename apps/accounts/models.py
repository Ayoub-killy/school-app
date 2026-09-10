from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        HEAD_OF_SCHOOL = 'HEAD_OF_SCHOOL', 'Head of School'
        ADMIN = 'ADMIN', 'Administrator'
        ACADEMIC_MASTER = 'ACADEMIC_MASTER', 'Academic Master'
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
        DEPARTMENT_STAFF = 'DEPARTMENT_STAFF', 'Department Staff'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    phone_number = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def has_role(self, *roles):
        """True if this is the user's primary role OR one of their extra roles."""
        if self.role in roles:
            return True
        return self.extra_roles.filter(role__in=roles).exists()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserRole(models.Model):
    """An additional role held by a user, beyond their primary role."""
    user = models.ForeignKey(User, related_name='extra_roles', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=User.Role.choices)
    department = models.ForeignKey(
        'sis.Department', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

import secrets
from django.utils import timezone
from datetime import timedelta


class StaffInvitation(models.Model):
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.Role.choices)
    department = models.ForeignKey(
        'sis.Department', null=True, blank=True, on_delete=models.SET_NULL
    )
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invitation for {self.email} ({self.get_role_display()})"
