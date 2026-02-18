from django.urls import path

from .views import (
    BatchScreenJobAPIView,
    ResumeResultAPIView,
    ResumeScreenAPIView,
    ResumeUploadAPIView,
)

urlpatterns = [
    path("upload/", ResumeUploadAPIView.as_view(), name="resume_upload"),
    path("screen/<int:resume_id>/", ResumeScreenAPIView.as_view(), name="resume_screen"),
    path("batch-screen/<int:job_id>/", BatchScreenJobAPIView.as_view(), name="batch_screen_job"),
    path("<int:id>/", ResumeResultAPIView.as_view(), name="resume_result"),
]
