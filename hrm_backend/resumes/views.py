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

    Upload a resume PDF and create:
    - Candidate (if not exists for this email + job)
    - Resume linked to candidate and job
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()
        return Response(
            {
                "message": "Resume uploaded successfully.",
                "resume_id": resume.id,
            },
            status=status.HTTP_201_CREATED,
        )


class ResumeScreenAPIView(APIView):
    """
    POST /api/resumes/screen/<resume_id>/

    Triggers mocked "AI screening" in a deterministic, explainable way:
    1) Extract skills from resume (mock static list)
    2) Compare with the job.required_skills
    3) Compute match score = (matched / required) * 100
    4) Decision: SHORTLISTED if score >= 60, else REJECTED
    5) Save results to Resume and update Candidate (match_score + status)
    """

    permission_classes = [IsAuthenticated, IsHROnly]

    def post(self, request, resume_id: int):
        try:
            resume = Resume.objects.select_related("candidate", "job").get(id=resume_id)
        except Resume.DoesNotExist:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

        job_required = _parse_required_skills(resume.job.required_skills)

        # -----------------------------
        # Mocked "skill extraction"
        # -----------------------------
        # For viva/defense: This is where an NLP/LLM pipeline would run.
        # We keep it deterministic using a fixed list of extracted skills.
        extracted = ["Python", "Django", "REST", "SQL", "Git", "Docker"]

        # Compare skills case-insensitively, but keep original casing from extracted list.
        required_lower = {s.lower() for s in job_required}
        matched = [s for s in extracted if s.lower() in required_lower]

        if job_required:
            score = (len(matched) / len(job_required)) * 100
        else:
            score = 0.0

        decision = Resume.DECISION_SHORTLISTED if score >= 60 else Resume.DECISION_REJECTED

        # Save screening results to Resume
        resume.extracted_skills = extracted
        resume.matched_skills = matched
        resume.match_score = round(score, 2)
        resume.decision = decision
        resume.screened_at = timezone.now()
        resume.save(
            update_fields=[
                "extracted_skills",
                "matched_skills",
                "match_score",
                "decision",
                "screened_at",
            ]
        )

        # Update candidate summary fields for the Candidate List page
        candidate: Candidate = resume.candidate
        candidate.match_score = resume.match_score
        candidate.status = decision  # Candidate status uses the same labels
        candidate.save(update_fields=["match_score", "status"])

        return Response(
            {
                "message": "Resume screened successfully.",
                "result": ResumeResultSerializer(resume).data,
            },
            status=status.HTTP_200_OK,
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

