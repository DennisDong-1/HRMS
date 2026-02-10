from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import HRRegistrationView, EmployeeRegistrationView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('register/hr/', HRRegistrationView.as_view()),
    path('register/employee/', EmployeeRegistrationView.as_view()),

]
