from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet

router = DefaultRouter()
router.register("", AttendanceViewSet, basename="attendance")

urlpatterns = [
    # /api/attendance/       -> list, create
    # /api/attendance/<pk>/  -> retrieve, update, delete
    path("", include(router.urls)),
]

