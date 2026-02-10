from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        # Set default values for superuser
        extra_fields.setdefault('full_name', 'Super Admin')
        extra_fields.setdefault('role', 'SUPERADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Check if role is being set correctly (optional validation)
        if extra_fields.get('role') != 'SUPERADMIN':
            raise ValueError('Superuser must have role=SUPERADMIN.')
        
        return self.create_user(email, password, **extra_fields)