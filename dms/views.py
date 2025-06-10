from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from scraapy.permissions import IsBusiness
from rest_framework.pagination import PageNumberPagination
from .models import Document, UserDocuments
from bms.models import OrderItem
from .serializers import DocumentSerializer, FilterDocumentSerializer,UserDocumentsSerializer,FilterUserDocumentSerializer, DocumentCreateSerializer
from django.db.models import Q
from external.pythonlibrary.api_responses.die import Response
from external.pythonlibrary.api_responses.error_types import ErrorTypes
from rest_framework import status
import datetime
from django.http import FileResponse
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class ProtectedDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, foldername, filename):
        part_path = os.path.join(foldername, filename)
        file_path = os.path.join(settings.PROTECTED_MEDIA_ROOT, part_path)
        documents = Document.objects.filter(Q(order_item__order__buyer = request.user) | Q(order_item__owner = request.user))
        if not documents:
            return Response(message="Error", errors={'type': ErrorTypes.NOT_FOUND, 'message': 'Document not found or no permissions'}, status=status.HTTP_404_NOT_FOUND)

        # Return the file as a response
        return FileResponse(open(file_path, 'rb'))
    
class DocumentList(ListAPIView):
    permission_classes = [IsBusiness]
    pagination_class = PageNumberPagination
    serializer_class = DocumentSerializer

    def get_queryset(self): 
        user = self.request.user        
        documents = Document.objects.filter(Q(order_item__order__buyer = user) | Q(order_item__owner = user))
        return documents

    def get(self, request):
        user = self.request.user
        if not user.has_business_profile:
            return Response(message="Business Profile", errors={'type': ErrorTypes.BAD_REQUEST,'message': 'You do not have a business profile'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.business_profile.status == request.user.business_profile.APPROVED:
            return Response(message="Business Profile", errors={'type': ErrorTypes.BAD_REQUEST,'message': 'Your business profile is not approved'}, status=status.HTTP_400_BAD_REQUEST)
            
        queryset = self.get_queryset()
        
        filterSerializer = FilterDocumentSerializer(data=request.GET)
        if not filterSerializer.is_valid():
            return Response(message="Validation error", errors=filterSerializer.errors, serializer=True, status=status.HTTP_400_BAD_REQUEST)

        if request.GET.get('type'):
            queryset = queryset.filter(type=request.GET.get('type'))
        if request.GET.get('query'):
            query = request.GET.get('query').lower().strip()
            queryset = queryset.filter(Q(id__icontains=query))

        # Time-based filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date:
            try:
                # Convert start_date to datetime
                start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(uploaded_at__gte=start_datetime)
            except ValueError:
                return Response({
                    "message": "Invalid start_date format. Use YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                # Convert end_date to datetime
                end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(uploaded_at__lte=end_datetime)
            except ValueError:
                return Response({
                    "message": "Invalid end_date format. Use YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)
            

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(message="Documents fetched successfully", data=serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        if not request.user.has_business_profile:
            return Response(message="Business Profile", errors={'type': ErrorTypes.BAD_REQUEST,'message': 'You do not have a business profile'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.business_profile.status == request.user.business_profile.APPROVED:
            return Response(message="Business Profile", errors={'type': ErrorTypes.BAD_REQUEST,'message': 'Your business profile is not approved'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DocumentCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(message="Validation error", errors=serializer.errors, serializer=True, status=status.HTTP_400_BAD_REQUEST)
        
        order_item = OrderItem.objects.get(pk = request.data["order_item"])
        if order_item.owner != request.user:
            return Response(message="No permissions", errors={'type': ErrorTypes.UNAUTHORIZED,'message': 'You are not authorized to perform this action'}, status=status.HTTP_401_UNAUTHORIZED)
        
        doc_serializer = serializer.save() 
        serializer = DocumentSerializer(doc_serializer)
        return Response(message="Document created successfully", data=serializer.data, status=status.HTTP_201_CREATED)


class UserDocumentList(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    serializer_class = UserDocumentsSerializer

    def get_queryset(self):
        user = self.request.user
        documents = UserDocuments.objects.filter(user=user).order_by('-created_at')
        return documents

    def get(self, request):
        queryset = self.get_queryset()
        filterSerializer = FilterUserDocumentSerializer(data=request.GET)
        if not filterSerializer.is_valid():
            return Response(message="Validation error", errors=filterSerializer.errors, serializer=True, status=status.HTTP_400_BAD_REQUEST)

        if request.GET.get('type'):
            queryset = queryset.filter(type=request.GET.get('type'))
        if request.GET.get('query'):
            query = request.GET.get('query').lower().strip().split('-')[-1]
            print(query)
            queryset = queryset.filter(Q(id__icontains=query))

        # Time-based filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date:
            try:
                # Convert start_date to datetime
                start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_datetime)
            except ValueError:
                return Response({
                    "message": "Invalid start_date format. Use YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                # Convert end_date to datetime
                end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__lte=end_datetime)
            except ValueError:
                return Response({
                    "message": "Invalid end_date format. Use YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True,context={"request": self.request.user})
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True,context={"request": self.request.user})
        return Response(message="Documents fetched successfully", data=serializer.data, status=status.HTTP_200_OK)
    