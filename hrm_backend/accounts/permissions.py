from rest_framework.permissions import BasePermission

from .models import User


def _get_user_role(request) -> str | None:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "role", None)


def has_role_at_least(user_role: str | None, required_role: str) -> bool:
    """
    Simple role hierarchy:
        SUPERADMIN > HR > EMPLOYEE
    """
    if user_role is None:
        return False

    hierarchy = {
        User.EMPLOYEE: 1,
        User.HR: 2,
        User.SUPERADMIN: 3,
    }
    return hierarchy.get(user_role, 0) >= hierarchy.get(required_role, 0)


class IsSuperAdmin(BasePermission):
    """
    Allows access only to SUPERADMIN users.
    """

    def has_permission(self, request, view):
        return _get_user_role(request) == User.SUPERADMIN


class IsHR(BasePermission):
    """
    Allows access to HR users and above (i.e. HR and SUPERADMIN).
    """

    def has_permission(self, request, view):
        role = _get_user_role(request)
        return has_role_at_least(role, User.HR)
