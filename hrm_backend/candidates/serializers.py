from rest_framework import serializers

from .models import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer for Candidate objects.

    - On create: HR provides full_name, email, applied_job, resume_path, etc.
    - On update: applied_job is kept read-only; HR can update status and match_score.
    """

    applied_job_title = serializers.ReadOnlyField(source="applied_job.title")

    class Meta:
        model = Candidate
        fields = [
            "id",
            "full_name",
            "email",
            "applied_job",
            "applied_job_title",
            "resume_path",
            "match_score",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_resume_path(self, value: str) -> str:
        """
        Ensure the resume is a PDF or DOCX file based on its path or filename.
        """
        if not value.lower().endswith((".pdf", ".docx")):
            raise serializers.ValidationError("Only PDF or DOCX resumes are allowed.")
        return value

    def validate_match_score(self, value):
        """
        Ensure the match score, if provided, is between 0 and 100.
        """
        if value is None:
            return value
        if not (0 <= value <= 100):
            raise serializers.ValidationError(
                "Match score must be between 0 and 100."
            )
        return value

    def update(self, instance, validated_data):
        """
        Prevent `applied_job` from being changed during updates.
        """
        validated_data.pop("applied_job", None)
        return super().update(instance, validated_data)

