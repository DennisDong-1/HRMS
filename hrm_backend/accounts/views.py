from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .permissions import IsSuperAdmin, IsHR
from .serializers import (
    ChangePasswordOnFirstLoginSerializer,
    EmployeeInviteSerializer,
    HRRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserSerializer,
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


def api_response(success: bool, message: str, data=None, errors=None, status_code=status.HTTP_200_OK):
    payload = {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
    }
    return Response(payload, status=status_code)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users and handling registration / password flows.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create_hr", "list", "retrieve"]:
            permission_classes = [IsAuthenticated, IsSuperAdmin]
        elif self.action in ["invite_employee"]:
            permission_classes = [IsAuthenticated, IsHR]
        elif self.action in ["forgot_password", "reset_password"]:
            permission_classes = [AllowAny]
        elif self.action in ["me", "change_password_first_login"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsSuperAdmin]
        return [perm() for perm in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "User list retrieved successfully", data=serializer.data)

    @action(detail=False, methods=["post"], url_path="register/hr")
    def create_hr(self, request):
        serializer = HRRegistrationSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return api_response(
                False,
                "Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        return api_response(True, "HR created successfully", data=UserSerializer(user).data, status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="register/employee")
    def invite_employee(self, request):
        """
        HR invites an employee. The employee will receive an email with a
        tokenised link to set their password and activate their account.
        """
        serializer = EmployeeInviteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return api_response(
                False,
                "Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Generate invitation link
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        invite_link = f"{frontend_url}/set-password/{uid}/{token}"

        # Send invitation email
        subject = "Welcome to HRMS - Set Your Password"
        message = (
            f"Hello {user.full_name},\n\n"
            f"You have been invited to join the HRMS system as an employee.\n"
            f"Please click the link below to set your password and activate your account:\n\n"
            f"{invite_link}\n\n"
            f"If you did not expect this email, please ignore it."
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return api_response(
            True,
            "Employee invited successfully. An invitation email has been sent.",
            data={"user": UserSerializer(user).data, "invite_link": invite_link},
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="forgot-password", permission_classes=[AllowAny])
    def forgot_password(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not reveal whether a user exists
            return api_response(True, "If that email exists, a reset link has been sent.")

        if not user.is_active or user.deactivated_at is not None:
            return api_response(True, "If that email exists, a reset link has been sent.")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"/reset-password/{uid}/{token}/"

        # TODO: Integrate with Django email backend to actually send the reset_link.
        return api_response(
            True,
            "If that email exists, a reset link has been sent.",
            data={"reset_link": reset_link},
        )

    @action(detail=False, methods=["post"], url_path="reset-password", permission_classes=[AllowAny])
    def reset_password(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid_int = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_int)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return api_response(False, "Invalid reset link.", status_code=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return api_response(False, "Invalid or expired reset token.", status_code=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.is_email_verified = True
        user.must_change_password = False
        user.save(update_fields=["password", "is_email_verified", "must_change_password"])

        return api_response(True, "Password has been reset successfully.")

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = UserSerializer(request.user)
        return api_response(True, "Current user retrieved successfully.", data=serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password-first-login")
    def change_password_first_login(self, request):
        user: User = request.user
        if not user.must_change_password:
            return api_response(False, "Password change on first login is not required.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = ChangePasswordOnFirstLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return api_response(True, "Password changed successfully.")
