from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Job
from .permissions import IsHRUser
from .serializers import JobSerializer


class JobListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing all jobs and creating new jobs.

    - GET  /api/jobs/  -> list all jobs (any authenticated user)
    - POST /api/jobs/  -> create a new job (HR users only)
    """

    queryset = Job.objects.select_related("created_by").all()
    serializer_class = JobSerializer

    def get_permissions(self):
        """
        Use different permissions based on the request method.
        - GET: Any authenticated user can list jobs
        - POST: Only HR users can create jobs
        """
        if self.request.method == "POST":
            permission_classes = [IsAuthenticated, IsHRUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Automatically set `created_by` from the authenticated HR user.
        """
        serializer.save(created_by=self.request.user)


class JobDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific job.

    - GET    /api/jobs/<id>/  -> retrieve job details (any authenticated user)
    - PUT    /api/jobs/<id>/  -> full update (HR users only)
    - PATCH  /api/jobs/<id>/  -> partial update (HR users only)
    - DELETE /api/jobs/<id>/  -> delete job (HR users only)
    """

    queryset = Job.objects.select_related("created_by").all()
    serializer_class = JobSerializer

    def get_permissions(self):
        """
        Use different permissions based on the request method.
        - GET: Any authenticated user can view job details
        - PUT/PATCH/DELETE: Only HR users can modify/delete jobs
        """
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated, IsHRUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


