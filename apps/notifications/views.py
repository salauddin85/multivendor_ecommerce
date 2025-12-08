
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from . import serializers
from . import models
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.activity_log.utils.functions import log_request
from config.utils.pagination import CustomPageNumberPagination
logger = logging.getLogger("myapp")



class CategoryView(APIView):

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return []

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.CategorySerializer(data=data)
            if serializer.is_valid():
                category = serializer.save()
                name = serializer.validated_data["name"]
                # log the request
                log_request(request, "Category created", "info",
                            f"Category '{name}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Category created successfully",
                    "status": "success",
                    "data": {
                        "id": category.id,
                        "name": name
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log the request
                log_request(request, "Category creation failed", "error",
                            "Category creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Category creation failed", "error", "Category creation failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            categories = models.Category.objects.all().order_by('-created_at')
            serializer = serializers.CategorySerializerForView(
                categories, many=True)
            # log the request
            log_request(request, "All categories fetched", "info",
                        "All categories fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "All categories fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "All categories fetch failed", "error", "All categories fetch failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SubscriberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.SubscriberSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                subscriber = serializer.save()
                email = serializer.validated_data["email"]
                # log the request
                log_request(request, "Subscriber created", "info",
                            f"Subscriber '{email}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Subscriber created successfully",
                    "status": "success",
                    "data": {
                        "id": subscriber.id,
                        "email": email
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log the request
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Invalid request",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Subscriber creation failed", "error", "Subscriber creation failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            notifications = models.Notification.objects.filter(user=request.user).order_by('-created_at')
            pagination = CustomPageNumberPagination()
            paginated_notifications = pagination.paginate_queryset(notifications, request)
            serializer = serializers.NotificationSerializer(paginated_notifications, many=True)
            # log the request
            log_request(request, "All notifications fetched", "info",
                        "All notifications fetched successfully", response_status_code=status.HTTP_200_OK)
            return pagination.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "All notifications fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "All notifications fetch failed", "error", "All notifications fetch failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Error occurred for notifications",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)