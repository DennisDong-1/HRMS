from django.urls import path

from .views import JobDetailAPIView, JobListCreateAPIView

urlpatterns = [
    # List all jobs and create new jobs
    # GET  /api/jobs/       -> list jobs (authenticated users)
    # POST /api/jobs/       -> create job (HR users only)
    path("", JobListCreateAPIView.as_view(), name="job-list-create"),
    
    # Retrieve, update, or delete a specific job
    # GET    /api/jobs/<pk>/  -> retrieve job details (authenticated users)
    # PUT    /api/jobs/<pk>/  -> full update (HR users only)
    # PATCH  /api/jobs/<pk>/  -> partial update (HR users only)
    # DELETE /api/jobs/<pk>/  -> delete job (HR users only)
    path("<int:pk>/", JobDetailAPIView.as_view(), name="job-detail"),
]


