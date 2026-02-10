from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model.

    Note:
    - The `created_by` field is read-only and always taken from the
      authenticated request user on the server side.
    """

    created_by = serializers.ReadOnlyField(source="created_by.email")

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "required_skills",
            "required_experience",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate_required_skills(self, value: str) -> str:
        """
        Ensure that at least one skill is provided.
        """
        skills = [s.strip() for s in value.split(",") if s.strip()]
        if not skills:
            raise serializers.ValidationError(
                "Please provide at least one required skill (comma separated)."
            )
        return ",".join(skills)

