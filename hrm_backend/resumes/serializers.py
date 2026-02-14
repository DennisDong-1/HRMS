from django.db import transaction
from rest_framework import serializers

from candidates.models import Candidate
from jobs.models import Job

from .models import Resume


class ResumeUploadSerializer(serializers.Serializer):
    """
    Handles the Resume Upload flow:
    - Validate inputs (PDF only)
    - Create Candidate record if it does not exist for (email, job)
    - Create Resume record linked to Candidate and Job
    """

    candidate_name = serializers.CharField(max_length=255)
    candidate_email = serializers.EmailField()
    job_id = serializers.IntegerField()
    resume_file = serializers.FileField()

    def validate_resume_file(self, file):
        # Simple PDF validation: check extension and (if present) the content-type.
        name = getattr(file, "name", "")
        content_type = getattr(file, "content_type", None)

        if not name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are allowed.")
        if content_type and content_type != "application/pdf":
            raise serializers.ValidationError("Only PDF files are allowed.")
        return file

    def validate_job_id(self, value: int) -> int:
        if not Job.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid job_id. Job does not exist.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        job = Job.objects.get(id=validated_data["job_id"])

        candidate, created = Candidate.objects.get_or_create(
            email=validated_data["candidate_email"],
            applied_job=job,
            defaults={
                "full_name": validated_data["candidate_name"],
                "resume_path": validated_data["resume_file"].name,
            },
        )

        # Keep candidate name updated if it changes across uploads.
        if not created and candidate.full_name != validated_data["candidate_name"]:
            candidate.full_name = validated_data["candidate_name"]

        candidate.resume_path = validated_data["resume_file"].name
        candidate.save(update_fields=["full_name", "resume_path"])

        resume = Resume.objects.create(
            candidate=candidate,
            job=job,
            resume_file=validated_data["resume_file"],
        )

        return resume


class ResumeResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.ReadOnlyField(source="candidate.full_name")
    candidate_email = serializers.ReadOnlyField(source="candidate.email")
    job_title = serializers.ReadOnlyField(source="job.title")
    job_required_skills = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id",
            "candidate_name",
            "candidate_email",
            "job",
            "job_title",
            "job_required_skills",
            "extracted_skills",
            "matched_skills",
            "match_score",
            "decision",
            "screened_at",
        ]
        read_only_fields = fields

    def get_job_required_skills(self, obj: Resume):
        # Return a normalized list of required skills from the Job model.
        raw = obj.job.required_skills or ""
        return [s.strip() for s in raw.split(",") if s.strip()]

