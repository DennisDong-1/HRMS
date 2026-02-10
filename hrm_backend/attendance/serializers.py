from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attendance

User = get_user_model()


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for Attendance records.

    Handles validation rules:
    - check_out, if provided, must be after check_in
    - employee must have role = EMPLOYEE
    - no duplicate attendance for the same employee + date
    """

    employee_full_name = serializers.ReadOnlyField(source="employee.full_name")
    marked_by_email = serializers.ReadOnlyField(source="marked_by.email")

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "employee_full_name",
            "date",
            "status",
            "check_in",
            "check_out",
            "marked_by",
            "marked_by_email",
            "created_at",
        ]
        read_only_fields = ["id", "marked_by", "marked_by_email", "created_at"]

    def validate_employee(self, value: User) -> User:
        """
        Ensure that the selected user is an EMPLOYEE.
        """
        employee_role = getattr(User, "EMPLOYEE", "EMPLOYEE")
        if getattr(value, "role", None) != employee_role:
            raise serializers.ValidationError(
                "Attendance can only be recorded for users with role EMPLOYEE."
            )
        return value

    def validate(self, attrs):
        """
        Object-level validation for time ordering and duplicate records.
        """
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")

        # Check that check_out is after check_in when both are provided.
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError(
                {"check_out": "Check-out time must be after check-in time."}
            )

        # Prevent duplicates: one record per employee per date.
        employee = attrs.get("employee") or getattr(self.instance, "employee", None)
        date = attrs.get("date") or getattr(self.instance, "date", None)

        if employee and date:
            qs = Attendance.objects.filter(employee=employee, date=date)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Attendance for this employee on this date already exists."
                )

        return attrs

