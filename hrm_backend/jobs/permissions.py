from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


class IsHRUser(BasePermission):
    """
    Allows access only to users with role = HR.

    This permission is designed to be combined with IsAuthenticated in views.
    """

    message = "Only HR users can perform this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        # Use the HR role constant if available, otherwise fall back to string.
        hr_role = getattr(User, "HR", "HR")
        return getattr(user, "role", None) == hr_role


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Read permissions are allowed for any request (GET, HEAD, OPTIONS).
    
    This is useful for allowing job creators to edit their own jobs,
    even if they're not HR users.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        # Read permissions are allowed to any request
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user


