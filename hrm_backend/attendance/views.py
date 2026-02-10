from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Attendance
from .permissions import IsHROnly
from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet exposing a simple REST API for manual attendance management.

    Endpoints (all HR-only):
    - POST   /api/attendance/        -> create attendance
    - GET    /api/attendance/        -> list attendance records
    - GET    /api/attendance/<id>/   -> retrieve a single record
    - PUT    /api/attendance/<id>/   -> update (if needed)
    - DELETE /api/attendance/<id>/   -> delete (if needed)
    """

    queryset = Attendance.objects.select_related("employee", "marked_by").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsHROnly]

    def perform_create(self, serializer):
        """
        Automatically set `marked_by` from the authenticated HR user.
        """
        serializer.save(marked_by=self.request.user)

