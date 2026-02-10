from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import HRRegistrationSerializer, EmployeeRegistrationSerializer
from .permissions import IsSuperAdmin, IsHR

class HRRegistrationView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = HRRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "HR created successfully"})


class EmployeeRegistrationView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request):
        serializer = EmployeeRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Employee registered successfully"})
