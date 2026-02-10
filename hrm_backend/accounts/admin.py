from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import EmployeeProfile, HRProfile, User, UserAuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("full_name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "deactivated_at",
                    "last_login_at",
                )
            },
        ),
        (
            _("Verification"),
            {
                "fields": (
                    "is_email_verified",
                    "must_change_password",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2", "role"),
            },
        ),
    )

    list_display = ("email", "full_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "full_name")
    ordering = ("email",)

    def get_readonly_fields(self, request, obj=None):
        """
        Prevent accidental role escalation in the admin.
        Only superusers may change the role; others see it as read-only.
        """
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly.append("role")
        return readonly

    def save_model(self, request, obj, form, change):
        """
        Log role changes and deactivations.
        """
        if change:
            old_obj = type(obj).objects.get(pk=obj.pk)
            if old_obj.role != obj.role:
                UserAuditLog.objects.create(
                    user=obj,
                    performed_by=request.user,
                    action=UserAuditLog.ACTION_ROLE_CHANGED,
                    metadata={"old_role": old_obj.role, "new_role": obj.role},
                )
            if old_obj.is_active and not obj.is_active:
                obj.deactivate(performed_by=request.user, reason="Deactivated via admin")
                return

        super().save_model(request, obj, form, change)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "position", "date_hired")
    search_fields = ("user__email", "user__full_name", "department", "position")


@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "office_location")
    search_fields = ("user__email", "user__full_name", "department", "office_location")


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "performed_by", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__email", "performed_by__email")
