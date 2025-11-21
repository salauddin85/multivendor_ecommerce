from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from . import models
from . import serializers
from apps.activity_log.utils.functions import log_request
import logging
logger = logging.getLogger("myapp")
from django.db import transaction
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from config.utils.pagination import CustomPageNumberPagination
from .filters import ProductFilter



#  ---------------------------------------------------------------------------

class ProductsView(APIView):
    
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            print(data)
            serializer = serializers.ProductSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, "Product created", "info", "Product created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Product created successfully",
                    "data": {
                        "id": instance.id,
                        "title": instance.title,
                        "price": instance.base_price,
                    }
                }, status=status.HTTP_201_CREATED)
            log_request(request, "Product creation failed", "warning", "Product creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Product creation failed due to invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product creation failed", "error", "Product creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product creation failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            products = models.Product.objects.select_related('store', 'category', 'brand').filter(status='draft')
            filter_set = ProductFilter(request.GET, queryset=products)
            products = filter_set.qs
            paginator = CustomPageNumberPagination()
            products = paginator.paginate_queryset(products, request, view=self)
            fields = request.GET.get('fields')
            if fields:
                fields = fields.split(',')
                serializer = serializers.ProductSerializerView(products, many=True, fields=fields)
            else:
                serializer = serializers.ProductSerializerView(products, many=True)

            log_request(request, "Products fetched", "info", "Products fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Products fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product fetch failed", "error", "Product fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product fetch failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return models.Product.objects.get(pk=pk)
        except models.Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            log_request(request, f"Product {pk} fetch failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductSerializer(product)
        log_request(request, f"Product {pk} fetched", "info", "Product fetched successfully", response_status_code=status.HTTP_200_OK)
        return Response({
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Product fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            log_request(request, f"Product {pk} update failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_request(request, f"Product {pk} updated", "info", "Product updated successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        log_request(request, f"Product {pk} update failed", "warning", "Product update failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
        return Response({
            "code": status.HTTP_400_BAD_REQUEST,
            "status": "fail",
            "message": "Product update failed due to invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            log_request(request, f"Product {pk} deletion failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        log_request(request, f"Product {pk} deleted", "info", "Product deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
        return Response({
            "code": status.HTTP_204_NO_CONTENT,
            "status": "success",
            "message": "Product deleted successfully",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)







