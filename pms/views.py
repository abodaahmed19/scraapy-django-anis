from django.contrib.auth import login
from django.db.models import Q
from .models import   BusinessProfile
from inventory.models import Category,LegalRequirements
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import DateTimeField
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import generics
from otp.models import PhoneOTP


from .serializers import UserCreateSerializer, UserSerializer 

from .serializers import (
   
    ProviderAuthSerializer,
    UserSerializer,
    BusinessProfileSerializer,
    BusinessProfileUpdateSerializer,
    BusinessProfileCRSerializer,
    NotificationSerializer,
    AddressSerializer,
    BusinessProfileIconSerializer,
    
)
from .models import User, BusinessProfile, Notification, Address
from external.pythonlibrary.api_responses.die import Response as Response_die
from external.pythonlibrary.api_responses.error_types import ErrorTypes
from scraapy.permissions import IsBusiness, IsStaff,IsBusinessOrIsStaff
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.social.views import ProviderAuthView
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from knox.settings import knox_settings

from inventory.models import Category
from django.contrib.auth import get_user_model

from .serializers import UserCreateSerializer, UserSerializer


User = get_user_model()

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]




class LoginView(KnoxLoginView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(LoginView, self).post(request, format=None)


class LoginSocialView(ProviderAuthView):
    serializer_class = ProviderAuthSerializer


class UserViewSet(DjoserUserViewSet):
    # override the activation method to login the user after activation
    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.is_active = True
        user.save()

        # create knox token
        instance, token = AuthToken.objects.create(user=user)

        data = {
            "expiry": DateTimeField(
                format=knox_settings.EXPIRY_DATETIME_FORMAT
            ).to_representation(instance.expiry),
            "token": token,
            "user": UserSerializer(user).data,
        }
        return Response(data=data, status=status.HTTP_200_OK)


class BusinessProfileView(APIView):
    permission_classes = [IsBusiness]

    def get(self, request):
        user = request.user
        try:
            business_profile = BusinessProfile.objects.get(user=user)
        except BusinessProfile.DoesNotExist:
            return Response_die(
                message="Business profile not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No Business profile found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BusinessProfileSerializer(business_profile)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.has_business_profile:
            return Response_die(
                message="Business",
                errors={
                    "type": ErrorTypes.NOT_ALLOWED,
                    "message": "You already have a business profile",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BusinessProfileCRSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response_die(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        print("this is business profile",request.data)
        try:
            business_profile = request.user.business_profile
        except BusinessProfile.DoesNotExist:
            return Response(
                {"error": "Business profile does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BusinessProfileUpdateSerializer(
            business_profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            print(serializer.errors)
            return Response_die(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        business_profile_serializer = serializer.save()
        serializer = BusinessProfileSerializer(business_profile_serializer)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserMeAPIView(APIView):
    permission_classes = [IsBusinessOrIsStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        # Tu peux adapter cette partie selon ce que tu veux retourner
        serializer = BusinessProfileIconSerializer(request.user.business_profile)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user  # L'utilisateur connecté
        serializer = BusinessProfileIconSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BusinessListApproveView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        users = User.objects.filter(business_profile__status=BusinessProfile.PENDING)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessDetailApproveView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, cr_number):
        business_profile = BusinessProfile.objects.filter(cr_number__exact=cr_number)
        if not business_profile.exists():
            return Response(
                {"error": "Business profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        business_profile = business_profile.first()
        if business_profile.status == BusinessProfile.APPROVED:
            return Response(
                {"error": "Business profile already approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        business_profile.status = BusinessProfile.APPROVED
        business_profile.save()
        user_serializer = UserSerializer(business_profile.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class BusinessDetailRejectView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, cr_number):
        business_profile = BusinessProfile.objects.filter(cr_number__exact=cr_number)
        if not business_profile.exists():
            return Response(
                {"error": "Business profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        business_profile = business_profile.first()
        if business_profile.status == BusinessProfile.REJECTED:
            return Response(
                {"error": "Business profile already rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        business_profile.status = BusinessProfile.REJECTED
        business_profile.save()
        user_serializer = UserSerializer(business_profile.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)

import uuid

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        notifications = Notification.objects.filter(user=user,is_read=True).order_by("-created_at")
        return notifications

    def get(self, request):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        notification_ids = request.data.get("notification_ids", [])
        if not notification_ids:
            return Response_die(
                message="Notification",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Provide notification ids",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        notifications = Notification.objects.filter(
            id__in=notification_ids, user=request.user
        )
        print("Notifications", notifications)
        if not notifications.exists():
            return Response_die(
                message="Notification",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No notifications found for these ids",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if notifications.filter(is_read=True).exists():
            return Response_die(
                message="Notification",
                errors={
                    "type": ErrorTypes.INVALID_INPUT,
                    "message": "All notifications are already read",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        notifications.update(is_read=True)  # Mark all as read

        return Response(status=status.HTTP_200_OK)
    

    def patch(self, request):
        print("this is notification",request.data)
        print("this is notification",request.data.get("id"))
        notification_id = request.data.get("id", None)
        if not notification_id:
            return Response_die(
                message="Notification",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Provide notification ids",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        notification = Notification.objects.get(pk=uuid.UUID(notification_id))
        if not notification:
            return Response_die(
                message="Notification",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No notification found for this id",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        notification.is_read = True
        notification.save() 
        return Response(status=status.HTTP_200_OK)




class AddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            addresses = user.addresses
        except Address.DoesNotExist:
            return Response_die(
                message="Address not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No address found for this user",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AddressSerializer(addresses, many=True)
        return Response_die(
            message="Address fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):

        data = request.data.copy()
        data["user"] = request.user.id

        serializer = AddressSerializer(data=data, context={"request": request})

        if not serializer.is_valid():
            return Response(
                {"message": "Validation error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()  # Save the address with the user
        return Response(
            {"message": "Address created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        user = request.user
        try:
            address = Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return Response_die(
                message="Address not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No address found for this user",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response_die(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        user = request.user
        try:
            address = Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return Response_die(
                message="Address not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No address found for this user",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        address.delete()
        return Response(status=status.HTTP_200_OK)


class LegalDataCheckView(APIView):
    permission_classes = [IsBusiness]

    def post(self, request):
        # Expecting payload like: {"id": [1,2,3]}
        category_ids = request.data.get("id", [])
        if not category_ids:
            return Response_die(
                {
                    "message": "No IDs provided",
                    "errors": {
                        "type": ErrorTypes.INVALID_INPUT,
                        "message": "No ID list provided in the request",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            business_profile = BusinessProfile.objects.get(user=request.user)
        except BusinessProfile.DoesNotExist:
            return Response_die(
                {
                    "message": "Business profile not found",
                    "errors": {
                        "type": ErrorTypes.NOT_FOUND,
                        "message": "No Business profile found",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        bp_serializer = BusinessProfileSerializer(business_profile)
        bp_data = bp_serializer.data

        result = []
        for cat_id in category_ids:
            try:
                category = Category.objects.get(id=cat_id)
            except Category.DoesNotExist:
                result.append(
                    {
                        "id": cat_id,
                        "message": "Category not found",
                        "LegalRequirements": [],
                    }
                )
                continue

            category_result = {
                "id": category.id,
                "name": category.name,
                "LegalRequirements": [],
            }

            for legalRequirement in category.legal_requirements.all():
                missing_fields = {}
                for req_field in legalRequirement.requirements or []:

                    field_value = bp_data.get(req_field)
                    if field_value in [None, ""]:
                        missing_fields[req_field] = field_value

                if missing_fields:
                    license_result = {
                        "id": legalRequirement.id,
                        "name": legalRequirement.name,
                        "missing_fields": (
                            missing_fields
                        ),
                    }
                    category_result["LegalRequirements"].append(license_result)

            result.append(category_result)
        return Response(data=result, status=status.HTTP_200_OK)
