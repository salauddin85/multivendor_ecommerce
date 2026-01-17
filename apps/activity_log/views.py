from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
import logging
from apps.activity_log.utils.functions import log_request
from . import serializers
from .models import *
from config.utils.pagination import CustomPageNumberPagination
from .utils.permissions import ActivityLogManagementPermission


logger = logging.getLogger("myapp")


class GetActivityLogView(APIView):
    """
        Get all activity log view
    """

    permission_classes = [IsAuthenticated, ActivityLogManagementPermission]

    def get(self, request):
        try:
            instances = ActivityLog.objects.all().order_by("-timestamp")
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(instances, request)
            serializer = serializers.AdminActivityLogSerializer(
                result_page, many=True)
            return paginator.get_paginated_response({
                "code": 200,
                "status": "success",
                "message": "All Activity log fetched successfully",
                "data": serializer.data
            }, status=200)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "operation failed due to server error",
                        "error", "operation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'errors': {
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'status': "failed",
                'message': "Error occurred",
                'errors': {
                    "server_error": [str(e)]
                }
            }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyActivityLogView(APIView):
    """
        Get own activity log view
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            instances = ActivityLog.objects.filter(user=request.user).order_by("-timestamp")
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(instances, request)
            serializer = serializers.ActivityLogSerializer(
                result_page, many=True)
            return paginator.get_paginated_response({
                "code": 200,
                "status": "success",
                "message": "Activity log fetched successfully",
                "data": serializer.data
            }, status=200)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "operation failed due to server error",
                        "error", "operation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'errors': {
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'status': "failed",
                'message': "Error occurred",
                'errors': {
                    "server_error": [str(e)]
                }
            }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)