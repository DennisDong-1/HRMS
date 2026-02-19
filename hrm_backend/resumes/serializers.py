from django.db import transaction
from rest_framework import serializers

from candidates.models import Candidate
from jobs.models import Job

from .models import Resume


class ResumeUploadSerializer(serializers.Serializer):
    """
    Handles the Resume Upload flow:
    - Validate inputs (PDF or DOCX)
    - Create Candidate record if it does not exist for (email, job)
    - Create Resume record linked to Candidate and Job
    """

    candidate_name = serializers.CharField(max_length=255)
    candidate_email = serializers.EmailField()
    job_id = serializers.IntegerField()
    resume_file = serializers.FileField()

    def validate_resume_file(self, file):
        name = getattr(file, "name", "")
        content_type = getattr(file, "content_type", None)

        allowed_extensions = (".pdf", ".docx")
        allowed_content_types = (
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        if not name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError("Only PDF and DOCX files are allowed.")
        if content_type and content_type not in allowed_content_types:
            raise serializers.ValidationError("Only PDF and DOCX files are allowed.")
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
            "ner_bonus",
            "decision",
            "screened_at",
            "error_message",
        ]
        read_only_fields = fields

    def get_job_required_skills(self, obj: Resume):
        # Return a normalized list of required skills from the Job model.
        raw = obj.job.required_skills or ""
        return [s.strip() for s in raw.split(",") if s.strip()]


class BatchUploadSerializer(serializers.Serializer):
    """
    Serializer for batch resume upload (multiple files for one job).
    """
    job_id = serializers.IntegerField()
    resume_files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
    )
    candidate_names = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False,
    )
    candidate_emails = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
    )

    def validate_job_id(self, value: int) -> int:
        if not Job.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid job_id. Job does not exist.")
        return value

    def validate(self, data):
        files = data.get("resume_files", [])
        names = data.get("candidate_names", [])
        emails = data.get("candidate_emails", [])
        if not (len(files) == len(names) == len(emails)):
            raise serializers.ValidationError(
                "resume_files, candidate_names, and candidate_emails must have the same length."
            )
        return data
