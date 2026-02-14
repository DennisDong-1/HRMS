from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Job(models.Model):
    """
    Represents an open job position in the HRM system.

    This model is intentionally simple and easy to understand for academic use.
    """

    title = models.CharField(max_length=255)
    required_skills = models.TextField(
        help_text="Comma-separated list of required skills, e.g. 'Python, Django, REST'"
    )
    required_experience = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Required experience in years (e.g. 3)",
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
        return f"{self.title} ({self.required_experience}+ yrs)"

