from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserAuditLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "is_active",
            "is_email_verified",
            "created_at",
            "deactivated_at",
            "last_login_at",
            "must_change_password",
        ]
        read_only_fields = [
            "id",
            "role",
            "is_active",
            "is_email_verified",
            "created_at",
            "deactivated_at",
            "last_login_at",
            "must_change_password",
        ]


class HRRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        request = self.context.get("request")
        performed_by = getattr(request, "user", None) if request else None

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            password=password,
            role=User.HR,
            is_email_verified=True,
        )

        UserAuditLog.objects.create(
            user=user,
            performed_by=performed_by,
            action=UserAuditLog.ACTION_CREATED,
            metadata={"role": user.role},
        )

        return user


class EmployeeInviteSerializer(serializers.ModelSerializer):
    """
    Serializer used when HR invites an employee.
    The employee will set their password via a tokenised link.
    """

    class Meta:
        model = User
        fields = ["email", "full_name"]

    def create(self, validated_data):
        request = self.context.get("request")
        performed_by = getattr(request, "user", None) if request else None

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            role=User.EMPLOYEE,
            must_change_password=True,
            is_active=True,
            is_email_verified=False,
        )

        UserAuditLog.objects.create(
            user=user,
            performed_by=performed_by,
            action=UserAuditLog.ACTION_CREATED,
            metadata={"role": user.role},
        )

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordOnFirstLoginSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customises the JWT payload and blocks inactive/deactivated users.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        user: User = self.user

        if not user.is_active or user.deactivated_at is not None:
            raise AuthenticationFailed(
                _("User account is inactive or deactivated."), code="user_inactive"
            )

        if not user.is_email_verified:
            raise AuthenticationFailed(
                _("Email address is not verified."), code="email_not_verified"
            )

        # Update last_login_at timestamp
        from django.utils import timezone

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at", "last_login"])

        data.update(
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "must_change_password": user.must_change_password,
            }
        )
        return data
