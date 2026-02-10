from django.urls import path

from .views import ResumeResultAPIView, ResumeScreenAPIView, ResumeUploadAPIView

urlpatterns = [
    path("upload/", ResumeUploadAPIView.as_view(), name="resume_upload"),
    path("screen/<int:resume_id>/", ResumeScreenAPIView.as_view(), name="resume_screen"),
    path("<int:id>/", ResumeResultAPIView.as_view(), name="resume_result"),
]

