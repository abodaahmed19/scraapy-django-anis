from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q



from external.pythonlibrary.api_responses.die import Response as Response_die
from external.pythonlibrary.api_responses.error_types import ErrorTypes
from scraapy.permissions import IsBusiness,IsBusinessComplete,IsDriver
from .serializers import DriverProfileSerializer,DriverProfileGetSerializer,OrderItemSerializer
from pms.serializers import UserSerializer
from pms.models import User
from .models import DriverProfile
from bms.models import OrderItem,OrderTracking
import random

class UserDriverView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessComplete]
    
    def post(self, request):
        if not request.user.has_business_profile:
            return Response_die(
                message="Unauthorized",
                errors={
                    "type": ErrorTypes.NOT_ALLOWED,
                    "message": "You must have a Business Profile to create a driver.",
                },
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = DriverProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            driver_profile=serializer.save()
            response = serializer.data
            response["password"] = driver_profile._generated_password
            return Response_die(message= "Driver created successfully",data = response, status=201)
            
        return Response_die(
            message="Validation Error",
            errors=serializer.errors,
            serializer=True,
            status=status.HTTP_400_BAD_REQUEST,
        )
    def get(self, request):
        if not request.user.has_business_profile:
            return Response_die(
                message="Unauthorized",
                errors={
                    "type": ErrorTypes.NOT_ALLOWED,
                    "message": "You must have a Business Profile to view drivers.",
                },
                status=status.HTTP_403_FORBIDDEN
            )
        drivers = DriverProfile.objects.filter(employer=request.user)

        serializer = DriverProfileGetSerializer(drivers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DriverRenewPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessComplete]
    
    def post(self, request):
        try:
            pk = request.data.get("pk")
            driver = DriverProfile.objects.get(pk=pk, employer=request.user)
        except DriverProfile.DoesNotExist:
            return Response_die(
                message="Not Found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Driver not found or you do not have permission to access it.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        new_password = str(random.randint(100000, 999999))
        driver.user.set_password(new_password)
        driver.user.save()

        return Response_die(
            message="Password reset successfully",
            data={"password": new_password},
            status=status.HTTP_200_OK
        )

class DeleteDriverView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessComplete]

    def delete(self, request, pk):
        try:
            driver = DriverProfile.objects.get(pk=pk, employer=request.user)
        except DriverProfile.DoesNotExist:
            return Response_die(
                message="Not Found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Driver not found or you do not have permission to delete it.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        driver.user.delete()  # حذف المستخدم المرتبط أيضًا
        driver.delete()       # حذف بروفايله

        return Response_die(
            message="Driver deleted successfully",
            data={},
            status=status.HTTP_200_OK
        )
    

class CustomPagination(PageNumberPagination):
    permission_classes = [IsAuthenticated, IsDriver] 
    page_size = 10  # Default per_page
    page_size_query_param = 'per_page'  # Matches frontend request
    max_page_size = 100

class DriverOrderDeliveryRequest(APIView):
    permission_classes = [IsAuthenticated, IsDriver] 
    pagination_class = CustomPagination  # Uses custom pagination
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        print("the user",self.request.user)
        print("the user",self.request.user.id)

        driver_profile = DriverProfile.objects.get(user=self.request.user)
        return OrderItem.objects.filter(
            owner=driver_profile.employer,
            order__shipping_option=1,
            # driver_tracking=None,
            tracking__status__in=[
                OrderTracking.READY,
                OrderTracking.STARTED_JOURNEY,
                OrderTracking.PICKED_UP,
                OrderTracking.DROP_OFF
            ]
        ).filter(
        Q(driver_tracking__isnull=True) | 
        Q(driver_tracking__driver=driver_profile)
    ).select_related('order', 'tracking', 'driver_tracking') 

    def get(self, request):
        print("the user",self.request.user)
        print("the user",self.request.user.id)
        queryset = self.get_queryset()
        



        # Paginate with ?page=X&per_page=Y support
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        serializer = self.serializer_class(page, many=True)
        
        return paginator.get_paginated_response({
            "message": "Orders fetched successfully",
            "data": serializer.data
        })