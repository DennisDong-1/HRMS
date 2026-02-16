from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Job(models.Model):
    """
    Represents a job posting in the HRM/Recruitment system.

    Tracks job positions from draft creation through to being filled,
    with support for department categorization, location specification,
    and flexible experience requirements (including fresher positions).
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        FILLED = "filled", "Filled"

    title = models.CharField(
        max_length=255,
        help_text="Job title, e.g. 'Senior Python Developer'"
    )
    description = models.TextField(
        help_text="Detailed job description including responsibilities and requirements"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department name, e.g. 'Engineering', 'Marketing', 'Sales'"
    )
    location = models.CharField(
        max_length=150,
        blank=True,
        help_text="Job location, e.g. 'Remote', 'Bengaluru (Hybrid)', 'New York Office'"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status of the job posting"
    )
    required_skills = models.TextField(
        help_text="Comma-separated list of required skills, e.g. 'Python, Django, REST'"
    )
    required_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Required experience in years (leave empty for fresher positions)",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs_created",
        help_text="The HR user who created this job.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        exp_text = f"{self.required_experience}+ yrs" if self.required_experience else "Fresher"
        return f"{self.title} ({exp_text}) - {self.get_status_display()}"

