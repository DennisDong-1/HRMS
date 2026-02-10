from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Job
from .permissions import IsHRUser
from .serializers import JobSerializer


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet providing a simple REST API for Job management.

    - POST   /api/jobs/        -> create job        (HR only)
    - GET    /api/jobs/        -> list jobs         (any authenticated user)
    - GET    /api/jobs/<id>/   -> retrieve job      (any authenticated user)
    - PUT    /api/jobs/<id>/   -> update job        (HR only)
    - PATCH  /api/jobs/<id>/   -> partial update    (HR only)
    - DELETE /api/jobs/<id>/   -> delete job        (HR only)
    """

    queryset = Job.objects.select_related("created_by").all()
    serializer_class = JobSerializer

    def get_permissions(self):
        """
        Use different permission rules based on the current action.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            # create, update, partial_update, destroy
            permission_classes = [IsAuthenticated, IsHRUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Automatically set `created_by` from the authenticated HR user.
        """
        serializer.save(created_by=self.request.user)

