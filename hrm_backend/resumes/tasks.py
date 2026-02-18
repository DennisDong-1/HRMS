"""
tasks.py
--------
Celery tasks for the resumes app.
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def screen_resume_task(self, resume_id: int):
    """
    Background Celery task: run ML screening for a single resume.

    Steps:
      1. Load Resume (with related Candidate and Job).
      2. Call run_ml_screening() from ml_inference.
      3. Update Resume fields: match_score, extracted_skills, matched_skills,
         decision, screened_at.
      4. Update Candidate fields: match_score, status.
      5. On any exception, save the error message to Resume.error_message
         and re-raise so Celery can retry / mark as FAILURE.
    """
    # Import here to avoid circular imports at module load time.
    from .ml_inference import run_ml_screening
    from .models import Resume

    logger.info("screen_resume_task started for resume_id=%s", resume_id)

    try:
        resume = Resume.objects.select_related("candidate", "job").get(id=resume_id)
    except Resume.DoesNotExist:
        logger.error("screen_resume_task: Resume %s not found.", resume_id)
        return  # Nothing to retry — the record simply doesn't exist.

    try:
        job_description = resume.job.description or ""
        resume_path = resume.resume_file.path  # absolute filesystem path

        result = run_ml_screening(resume_path, job_description)

        # --- Update Resume ---
        resume.match_score = result["score"]
        resume.extracted_skills = result["extracted_skills"]
        resume.matched_skills = result["matched_skills"]
        resume.decision = result["decision"]
        resume.screened_at = timezone.now()
        resume.error_message = ""  # clear any previous error
        resume.save(
            update_fields=[
                "match_score",
                "extracted_skills",
                "matched_skills",
                "decision",
                "screened_at",
                "error_message",
            ]
        )

        # --- Update Candidate ---
        candidate = resume.candidate
        candidate.match_score = result["score"]
        candidate.status = result["decision"]
        candidate.save(update_fields=["match_score", "status"])

        logger.info(
            "screen_resume_task completed for resume_id=%s: score=%.2f decision=%s",
            resume_id,
            result["score"],
            result["decision"],
        )

    except Exception as exc:
        # Persist error so HR can see what went wrong via the result endpoint.
        try:
            resume.error_message = str(exc)
            resume.save(update_fields=["error_message"])
        except Exception:
            pass  # Don't mask the original exception.

        logger.exception(
            "screen_resume_task failed for resume_id=%s: %s", resume_id, exc
        )
        raise self.retry(exc=exc)
