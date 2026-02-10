from django.db import models

from jobs.models import Job


class Candidate(models.Model):
    """
    Represents a job applicant.

    Note that candidates are NOT authenticated users in the system.
    """

    STATUS_PENDING = "PENDING"
    STATUS_SHORTLISTED = "SHORTLISTED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SHORTLISTED, "Shortlisted"),
        (STATUS_REJECTED, "Rejected"),
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    applied_job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="candidates",
        help_text="The job the candidate applied for.",
    )
    # For simplicity we store a path/string to the uploaded resume.
    # In a real system this would likely be a FileField with configured storage.
    resume_path = models.CharField(
        max_length=512,
        help_text="Path or identifier for the candidate's resume (PDF only).",
    )
    match_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Optional match score in percentage (0-100).",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} -> {self.applied_job}"

