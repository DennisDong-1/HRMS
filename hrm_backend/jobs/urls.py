from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JobViewSet

router = DefaultRouter()
router.register("", JobViewSet, basename="job")

urlpatterns = [
    # This will expose:
    #   /api/jobs/       -> list, create
    #   /api/jobs/<pk>/  -> retrieve, update, delete
    path("", include(router.urls)),
]

