from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model.

    Note:
    - The `created_by` field is read-only and always taken from the
      authenticated request user on the server side.
    - The `is_owner` field indicates whether the current user created this job.
    """

    created_by = serializers.ReadOnlyField(source="created_by.email")
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "department",
            "location",
            "status",
            "required_skills",
            "required_experience",
            "created_by",
            "created_at",
            "is_owner",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def get_is_owner(self, obj) -> bool:
        """
        Check if the current request user is the creator of this job.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.created_by == request.user
        return False

    def validate_description(self, value: str) -> str:
        """
        Ensure description is not empty or just whitespace.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Job description cannot be empty or contain only whitespace."
            )
        return value.strip()

    def validate_required_skills(self, value: str) -> str:
        """
        Ensure that at least one skill is provided.
        Normalizes the comma-separated list.
        """
        skills = [s.strip() for s in value.split(",") if s.strip()]
        if not skills:
            raise serializers.ValidationError(
                "Please provide at least one required skill (comma separated)."
            )
        return ",".join(skills)


