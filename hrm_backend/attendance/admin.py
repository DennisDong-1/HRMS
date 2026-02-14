from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Attendance model.
    """

    list_display = (
        "employee",
        "date",
        "status",
        "check_in",
        "check_out",
        "marked_by",
        "created_at",
    )
    search_fields = ("employee__email", "employee__full_name")
    list_filter = ("status", "date", "marked_by")

