from django.db import models

from candidates.models import Candidate
from jobs.models import Job


class Resume(models.Model):
    """
    Stores a candidate's uploaded resume, and the mocked AI screening results.
    """

    DECISION_SHORTLISTED = "SHORTLISTED"
    DECISION_REJECTED = "REJECTED"

    DECISION_CHOICES = (
        (DECISION_SHORTLISTED, "Shortlisted"),
        (DECISION_REJECTED, "Rejected"),
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    resume_file = models.FileField(upload_to="resumes/")

    # These fields store mocked "AI" results. We use JSON arrays for simplicity.
    extracted_skills = models.JSONField(default=list, blank=True)
    matched_skills = models.JSONField(default=list, blank=True)

    match_score = models.FloatField(default=0)
    decision = models.CharField(
        max_length=20, choices=DECISION_CHOICES, null=True, blank=True
    )
    screened_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-screened_at", "-id"]

    def __str__(self) -> str:
        return f"Resume({self.candidate.full_name} -> {self.job.title})"

