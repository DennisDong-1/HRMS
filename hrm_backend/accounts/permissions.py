from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'SUPERADMIN'


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'HR'
