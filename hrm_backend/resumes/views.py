from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.models import Candidate

from .models import Resume
from .permissions import IsHROnly
from .serializers import ResumeResultSerializer, ResumeUploadSerializer


def _parse_required_skills(required_skills: str) -> list[str]:
    """
    Convert a comma-separated skills string into a cleaned list.
    """
    return [s.strip() for s in (required_skills or "").split(",") if s.strip()]


class ResumeUploadAPIView(APIView):
    """
    POST /api/resumes/upload/

    Upload a resume PDF/DOCX and create:
    - Candidate (if not exists for this email + job)
    - Resume linked to candidate and job

    After saving, automatically dispatches the ML screening Celery task.
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()

        # Trigger background ML screening task
        from .tasks import screen_resume_task
        screen_resume_task.delay(resume.id)

        return Response(
            {
                "message": "Resume uploaded successfully. ML screening has been queued.",
                "resume_id": resume.id,
            },
            status=status.HTTP_201_CREATED,
        )


class ResumeScreenAPIView(APIView):
    """
    POST /api/resumes/screen/<resume_id>/

    Manual trigger for ML screening of a specific resume.
    Dispatches the Celery task and returns immediately.
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def post(self, request, resume_id: int):
        try:
            resume = Resume.objects.select_related("candidate", "job").get(id=resume_id)
        except Resume.DoesNotExist:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

        from .tasks import screen_resume_task
        screen_resume_task.delay(resume.id)

        return Response(
            {
                "message": f"ML screening task queued for resume {resume_id}.",
                "resume_id": resume_id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class BatchScreenJobAPIView(APIView):
    """
    POST /api/resumes/batch-screen/<job_id>/

    Queues ML screening tasks for all unscreened resumes belonging to a job.
    An "unscreened" resume is one where screened_at is null.
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def post(self, request, job_id: int):
        from .tasks import screen_resume_task

        unscreened = Resume.objects.filter(job_id=job_id, screened_at__isnull=True)
        count = unscreened.count()

        if count == 0:
            return Response(
                {"message": "No unscreened resumes found for this job."},
                status=status.HTTP_200_OK,
            )

        for resume in unscreened:
            screen_resume_task.delay(resume.id)

        return Response(
            {
                "message": f"Queued ML screening for {count} resume(s).",
                "queued_count": count,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ResumeResultAPIView(APIView):
    """
    GET /api/resumes/<id>/

    Retrieve the screening result for a resume.
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def get(self, request, id: int):
        try:
            resume = Resume.objects.select_related("candidate", "job").get(id=id)
        except Resume.DoesNotExist:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(ResumeResultSerializer(resume).data, status=status.HTTP_200_OK)
