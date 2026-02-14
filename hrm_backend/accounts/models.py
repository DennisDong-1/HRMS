from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the HRM system.

    NOTE: Existing fields must not be changed in a way that breaks
    the initial migration. New fields are only appended.
    """

    # Role constants and choices
    SUPERADMIN = "SUPERADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"

    ROLE_CHOICES = (
        (SUPERADMIN, "Super Admin"),
        (HR, "HR"),
        (EMPLOYEE, "Employee"),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    # New fields (added after initial migration)
    is_email_verified = models.BooleanField(default=False)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(
        default=False,
        help_text="If True, user must change password on next login.",
    )

    objects = UserManager()

    # configuration hooks, Django reads during auth and user creation
    USERNAME_FIELD = "email"  # uniquely identifies user for login
    REQUIRED_FIELDS = ["full_name", "role"]  # asked for when creating a superuser

    def __str__(self) -> str:
        return self.email

    def deactivate(self, performed_by=None, reason: str | None = None) -> None:
        """
        Soft-deactivate the user instead of deleting.
        """
        if not self.is_active:
            return

        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=["is_active", "deactivated_at"])

        # Lazy import to avoid circulars
        from .models import UserAuditLog  # type: ignore  # noqa

        UserAuditLog.objects.create(
            user=self,
            performed_by=performed_by,
            action=UserAuditLog.ACTION_DEACTIVATED,
            metadata={"reason": reason} if reason else {},
        )

    def delete(self, using=None, keep_parents=False):
        """
        Override hard delete with soft-deactivation.
        """
        self.deactivate()


class EmployeeProfile(models.Model):
    """
    HR-specific data for employees.
    Auth-related information remains on the User model.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    department = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)
    date_hired = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f"EmployeeProfile({self.user.email})"


class HRProfile(models.Model):
    """
    HR-specific data for HR users.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hr_profile",
    )
    department = models.CharField(max_length=255, blank=True)
    office_location = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"HRProfile({self.user.email})"


class UserAuditLog(models.Model):
    """
    Simple audit log for user lifecycle events.
    """

    ACTION_CREATED = "CREATED"
    ACTION_ROLE_CHANGED = "ROLE_CHANGED"
    ACTION_DEACTIVATED = "DEACTIVATED"

    ACTION_CHOICES = (
        (ACTION_CREATED, "User created"),
        (ACTION_ROLE_CHANGED, "Role changed"),
        (ACTION_DEACTIVATED, "User deactivated"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_audit_logs",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} - {self.user.email}"
