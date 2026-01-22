from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAdminUser
from rest_framework import status
import logging
from apps.activity_log.utils.functions import log_request
from . import serializers
from .models import *
from config.utils.pagination import CustomPageNumberPagination
from apps.authentication.models import Customer
from apps.products.models import Product,ProductVariant
logger = logging.getLogger("myapp")


class AllProductsView(APIView):
    """
        Get all products requests view
    """

    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            instances = Product.objects.select_related('brand','category','store').all().order_by("id")
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(instances, request)
            serializer = serializers.AllProductSerializer(
                result_page, many=True)
            return paginator.get_paginated_response({
                "code": 200,
                "status": "success",
                "message": "All products fetched successfully",
                "data": serializer.data
            }, status=200)
        except Exception as e:
            logging.exception(str(e))
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
            
class AllVariantsView(APIView):
    """
        Get all variants requests view
    """

    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            instances = ProductVariant.objects.select_related('product').all().order_by("id")
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(instances, request)
            serializer = serializers.AllProductVariantSerializer(
                result_page, many=True)
            return paginator.get_paginated_response({
                "code": 200,
                "status": "success",
                "message": "All product variants fetched successfully",
                "data": serializer.data
            }, status=200)
        except Exception as e:
            logging.exception(str(e))
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