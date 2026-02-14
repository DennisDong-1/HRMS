from rest_framework.permissions import BasePermission

from jobs.permissions import IsHRUser


class IsHROnly(BasePermission):
    """
    Restricts access to HR users only.

    This wraps the shared IsHRUser permission from the jobs app so the
    attendance app remains self-explanatory and consistent.
    """

    message = "Only HR users can manage attendance records."

    def has_permission(self, request, view) -> bool:
        return IsHRUser().has_permission(request, view)

