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
    # permission_classes = [IsAuthenticated]

    def get_object(self, slug):
        try:
            return models.Product.objects.select_related('store', 'category', 'brand').get(slug=slug)
        except models.Product.DoesNotExist:
            return None

    def get(self, request, slug):
        product = self.get_object(slug)
        if not product:
            log_request(request, f"Product {slug} fetch failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found",
                "data": {
                    "product": f"Product not found{slug}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductDetailSerializer(product)
        log_request(request, f"Product {slug} fetched", "info", "Product fetched successfully", response_status_code=status.HTTP_200_OK)
        return Response({
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Product fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        product = self.get_object(slug)
        if not product:
            log_request(request, f"Product {slug} update failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found",
                "data": {
                    "product": f"Product not found{slug}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            log_request(request, f"Product {slug} updated", "info", "Product updated successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product updated successfully",
                "data": {
                    "id": instance.id,
                    "title": instance.title,
                    "price": instance.base_price,
                }
            }, status=status.HTTP_200_OK)
        log_request(request, f"Product {slug} update failed", "warning", "Product update failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
        return Response({
            "code": status.HTTP_400_BAD_REQUEST,
            "status": "failed",
            "message": "Product update failed due to invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        product = self.get_object(slug)
        if not product:
            log_request(request, f"Product {slug} deletion failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product not found",
                "data": {
                    "product": f"Product not found {slug}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        log_request(request, f"Product {slug} deleted", "info", "Product deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
        return Response({
            "code": status.HTTP_204_NO_CONTENT,
            "status": "success",
            "message": "Product deleted successfully",
           
        }, status=status.HTTP_204_NO_CONTENT)


class ProductAttributeView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.ProductAttributeSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, "Product attribute created", "info", "Product attribute created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Product attribute created successfully",
                    "data": {
                        "id": instance.id,
                        "name": instance.name,
                        "product": instance.product.title,
                    }
                }, status=status.HTTP_201_CREATED)
            log_request(request, "Product attribute creation failed", "warning", "Product attribute creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Product attribute creation failed due to invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product attribute creation failed", "error", "Product attribute creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product attribute creation failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            product_attributes = models.ProductAttribute.objects.select_related('product').all()
            paginator = CustomPageNumberPagination()
            product_attributes = paginator.paginate_queryset(product_attributes, request, view=self)
            serializer = serializers.ProductAttributeSerializer(product_attributes, many=True)
            log_request(request, "Product attributes fetched", "info", "Product attributes fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attributes fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product attribute fetch failed", "error", "Product attribute fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product attribute fetch failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductAttributeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return models.ProductAttribute.objects.select_related('product').get(pk=pk)
        except models.ProductAttribute.DoesNotExist:
            return None

    def get(self, request, pk):
        product_attribute = self.get_object(pk)
        if not product_attribute:
            log_request(request, f"Product attribute {pk} fetch failed", "warning", "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductAttributeSerializer(product_attribute)
        log_request(request, f"Product attribute {pk} fetched", "info", "Product attribute fetched successfully", response_status_code=status.HTTP_200_OK)
        return Response({
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Product attribute fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        product_attribute = self.get_object(pk)
        if not product_attribute:
            log_request(request, f"Product attribute {pk} update failed", "warning", "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ProductAttributeSerializer(product_attribute, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            log_request(request, f"Product attribute {pk} updated", "info", "Product attribute updated successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attribute updated successfully",
                "data": {
                    "id": instance.id,
                    "name": instance.name,
                    "product": instance.product.title,
                }
            }, status=status.HTTP_200_OK)
        log_request(request, f"Product attribute {pk} update failed", "warning", "Product attribute update failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
        return Response({
            "code": status.HTTP_400_BAD_REQUEST,
            "status": "failed",
            "message": "Product attribute update failed due to invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product_attribute = self.get_object(pk)
        if not product_attribute:
            log_request(request, f"Product attribute {pk} deletion failed", "warning", "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        product_attribute.delete()
        log_request(request, f"Product attribute {pk} deleted", "info", "Product attribute deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
        return Response({
            "code": status.HTTP_204_NO_CONTENT,
            "status": "success",
            "message": "Product attribute deleted successfully",
        }, status=status.HTTP_204_NO_CONTENT)
