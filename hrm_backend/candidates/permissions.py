from rest_framework.permissions import BasePermission

from jobs.permissions import IsHRUser


class IsHROnly(BasePermission):
    """
    Thin wrapper around the IsHRUser permission from the jobs app.

    This keeps the candidates app self-explanatory while reusing the
    existing HR role logic.
    """

    message = "Only HR users can manage candidates."

    def has_permission(self, request, view) -> bool:
        return IsHRUser().has_permission(request, view)

