from rest_framework.permissions import BasePermission

from jobs.permissions import IsHRUser


class IsHROnly(BasePermission):
    """
    HR-only access for resume upload/screening/results.
    Reuses the existing HR role check from the jobs app.
    """

    message = "Only HR users can access resume screening features."

    def has_permission(self, request, view) -> bool:
        return IsHRUser().has_permission(request, view)

