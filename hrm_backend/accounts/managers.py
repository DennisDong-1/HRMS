from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """
    Custom manager for User model that centralises role validation logic.
    """

    def _validate_role(self, role: str) -> None:
        from .models import User

        valid_roles = {User.SUPERADMIN, User.HR, User.EMPLOYEE}
        if role not in valid_roles:
            raise ValidationError(f"Invalid role '{role}'. Must be one of {valid_roles}.")

    def create_user(self, email, password=None, **extra_fields):
        from .models import User  # local import to avoid circulars

        if not email:
            raise ValueError("Email is required")

        role = extra_fields.get("role", User.EMPLOYEE)
        self._validate_role(role)
        extra_fields["role"] = role

        # Normalise email
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            # For invited users we initially create an account without a password.
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        from .models import User  # local import to avoid circulars

        if not password:
            raise ValueError("Superuser must have a password.")

        # Enforce correct role and privilege flags
        extra_fields.setdefault("full_name", "Super Admin")
        extra_fields.setdefault("role", User.SUPERADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True) 

        if extra_fields.get("role") != User.SUPERADMIN:
            raise ValueError("Superuser must have role=SUPERADMIN.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)