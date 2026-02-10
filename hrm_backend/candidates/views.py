from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Candidate
from .permissions import IsHROnly
from .serializers import CandidateSerializer


class CandidateViewSet(viewsets.ModelViewSet):
    """
    ViewSet exposing a simple REST API to manage candidates.

    All endpoints are restricted to authenticated HR users:
    - POST   /api/candidates/        -> create candidate
    - GET    /api/candidates/        -> list candidates
    - GET    /api/candidates/<id>/   -> retrieve candidate
    - PUT    /api/candidates/<id>/   -> update status/match_score
    - PATCH  /api/candidates/<id>/   -> partial update
    """

    queryset = Candidate.objects.select_related("applied_job").all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated, IsHROnly]

