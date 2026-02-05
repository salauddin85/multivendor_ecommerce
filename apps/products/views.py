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
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from config.utils.pagination import CustomPageNumberPagination
from .filters import ProductFilter
from django.db.models import Prefetch, Count, Subquery, OuterRef,Q,Sum

from apps.orders.models import OrderItem
from apps.catalog.models import Category
from decimal import Decimal





#  ---------------------------------------------------------------------------

class ProductsView(APIView):
    
    # def get_permissions(self):
    #     if self.request.method == 'POST':
    #         return [IsAdminUser()]  
    #     else:
    #         return [AllowAny()]  
    
    def post(self, request):
        try:
            data = request.data
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
            queryset = (
                models.Product.objects
                .select_related("store", "category", "brand")
                .filter(status="published")
            )

            filters = Q()

            brand = request.GET.get("brand")
            category = request.GET.get("category")
            search = request.GET.get("search")
            store = request.GET.get("store")
            min_price = request.GET.get("min_price")
            max_price = request.GET.get("max_price")
            new_arrival = request.GET.get("new_arrival", "").lower() == "true"


            if brand:
                filters &= Q(brand__slug=brand)

            if category:
                filters &= Q(category__slug=category)

            if search:
                filters &= Q(title__icontains=search)

            if store:
                filters &= Q(store__store_name__icontains=store)

            if min_price:
                filters &= Q(base_price__gte=Decimal(min_price))
            if max_price:
                filters &= Q(base_price__lte=Decimal(max_price))

            queryset = queryset.filter(filters)
            if new_arrival:
                queryset = queryset.order_by("-created_at")
            else:
                queryset = queryset.order_by("id")

            paginator = CustomPageNumberPagination()
            products = paginator.paginate_queryset(queryset, request, view=self)

            serializer = serializers.ProductSerializerView(products, many=True)

            return paginator.get_paginated_response({
                "code": 200,
                "status": "success",
                "message": "Products fetched successfully",
                "data": serializer.data
            })

        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": 500,
                "status": "error",
                "message": "Product fetch failed",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=500)



class ProductsDetailView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        try:
            product = models.Product.objects.select_related(
                "store", "category", "brand"
            ).prefetch_related(
                "images", "attributes", "variants"
            ).get(slug=slug)

            # ==============================
            # Session based view count logic
            # ==============================
            session_key = f"viewed_product_{product.id}"

            if not request.session.get(session_key):
                with transaction.atomic():
                    product.view_count += 1
                    product.save(update_fields=["view_count"])
                    request.session[session_key] = True

            serializer = serializers.ProductDetailSerializer(product)

            log_request(
                request,
                f"Product {slug} fetched",
                "info",
                "Product fetched successfully",
                response_status_code=status.HTTP_200_OK
            )

            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product {slug} fetch failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                f"Product {slug} fetch failed",
                "error",
                f"Server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Invalid request",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def patch(self, request, slug):
        try:
            product = models.Product.objects.get(slug=slug)

            serializer = serializers.ProductSerializer(
                product, data=request.data, partial=True)

            if serializer.is_valid():
                instance = serializer.save()

                log_request(
                    request,
                    f"Product {slug} updated",
                    "info",
                    "Product updated successfully",
                    response_status_code=status.HTTP_200_OK
                )

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

            log_request(
                request,
                f"Product {slug} update failed",
                "warning",
                "Invalid data",
                response_status_code=status.HTTP_400_BAD_REQUEST
            )

            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product {slug} update failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                f"Product {slug} update failed",
                "error",
                f"Server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": { "server_error": [str(e)] }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, slug):
        try:
            product = models.Product.objects.get(slug=slug)
            product.delete()

            log_request(
                request,
                f"Product {slug} deleted",
                "info",
                "Product deleted successfully",
                response_status_code=status.HTTP_204_NO_CONTENT
            )

            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)

        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product {slug} delete failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )

            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                f"Product {slug} delete failed",
                "error",
                f"Server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": { "server_error": [str(e)] }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            serializer = serializers.ProductAttributeSerializerForView(product_attributes, many=True)
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

    def get(self, request, pk):
        try:
            pa = models.ProductAttribute.objects.select_related('product').get(pk=pk)
            serializer = serializers.ProductAttributeSerializerDetailView(pa)
            log_request(request, f"Product attribute {pk} fetched", "info",
                        "Product attribute fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attribute fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except models.ProductAttribute.DoesNotExist:
            log_request(request, f"Product attribute {pk} fetch failed", "warning",
                        "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute {pk} fetch failed", "error",
                        f"Product attribute fetch failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            pa = models.ProductAttribute.objects.select_related('product').get(pk=pk)
            serializer = serializers.ProductAttributeSerializer(pa, data=request.data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, f"Product attribute {pk} updated", "info",
                            "Product attribute updated successfully", response_status_code=status.HTTP_200_OK)
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
            else:
                log_request(request, f"Product attribute {pk} update failed", "warning",
                            "Product attribute update failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Product attribute update failed due to invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except models.ProductAttribute.DoesNotExist:
            log_request(request, f"Product attribute {pk} update failed", "warning",
                        "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute {pk} update failed", "error",
                        f"Product attribute update failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            pa = models.ProductAttribute.objects.get(pk=pk)
            pa.delete()
            log_request(request, f"Product attribute {pk} deleted", "info",
                        "Product attribute deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product attribute deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)

        except models.ProductAttribute.DoesNotExist:
            log_request(request, f"Product attribute {pk} deletion failed", "warning",
                        "Product attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found",
                "data": {
                    "product_attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute {pk} deletion failed", "error",
                        f"Product attribute deletion failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductSpecificAttributeView(APIView):
    
    def get(self, request, slug):
        try:
            product = models.Product.objects.prefetch_related('attributes').get(slug=slug)
            product_attributes = product.attributes.all()
            
            serializer = serializers.ProductAttributeSerializer(product_attributes, many=True)
            log_request(
                request,
                f"Product {slug} specific attributes fetched",
                "info",
                "Product specific attributes fetched successfully",
                response_status_code=status.HTTP_200_OK
            )
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product specific attributes fetched successfully",
                "data": serializer.data # Assuming ProductDetailSerializer has an 'attributes' field
            }, status=status.HTTP_200_OK)
        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product {slug} specific attributes fetch failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found",
                "data": {
                    "product": f"Product not found with slug {slug}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                f"Product {slug} specific attributes fetch failed",
                "error",
                f"Server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": { "server_error": [str(e)] }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
class ProductAttributeValuesView(APIView): 
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.ProductAttributeValueSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, "Product attribute value created", "info", "Product attribute value created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Product attribute value created successfully",
                    "data": {
                        "id": instance.id,
                        "value": instance.value,
                        "attribute": instance.attribute.name,
                    }
                }, status=status.HTTP_201_CREATED)
            log_request(request, "Product attribute value creation failed", "warning", "Product attribute value creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Product attribute value creation failed due to invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product attribute value creation failed", "error", "Product attribute value creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product attribute value creation failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            product_attribute_values = models.ProductAttributeValue.objects.select_related('attribute').all()
            paginator = CustomPageNumberPagination()
            product_attribute_values = paginator.paginate_queryset(product_attribute_values, request, view=self)
            serializer = serializers.ProductAttributeValueSerializer(product_attribute_values, many=True)
            log_request(request, "Product attribute values fetched", "info", "Product attribute values fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attribute values fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product attribute value fetch failed", "error", "Product attribute value fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product attribute value fetch failed due to server error",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductAttributeValuesDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            pav = models.ProductAttributeValue.objects.select_related('attribute').get(pk=pk)
            serializer = serializers.ProductAttributeValueSerializer(pav)
            log_request(request, f"Product attribute value {pk} fetched", "info",
                        "Product attribute value fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attribute value fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except models.ProductAttributeValue.DoesNotExist:
            
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute value not found",
                "data": {
                    "product_attribute_value": f"Product attribute value not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute value {pk} fetch failed", "error",
                        f"Product attribute value fetch failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            pav = models.ProductAttributeValue.objects.select_related('attribute').get(pk=pk)
            serializer = serializers.ProductAttributeValueSerializer(pav, data=request.data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, f"Product attribute value {pk} updated", "info",
                            "Product attribute value updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Product attribute value updated successfully",
                    "data": {
                        "id": instance.id,
                        "value": instance.value,
                        "attribute": instance.attribute.name
                    }
                }, status=status.HTTP_200_OK)
            else:
                log_request(request, f"Product attribute value {pk} update failed", "warning",
                            "Product attribute value update failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Product attribute value update failed due to invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except models.ProductAttributeValue.DoesNotExist:
            log_request(request, f"Product attribute value {pk} update failed", "warning",
                        "Product attribute value not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute value not found",
                "data": {
                    "product_attribute_value": f"Product attribute value not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute value {pk} update failed", "error",
                        f"Product attribute value update failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            pav = models.ProductAttributeValue.objects.get(pk=pk)
            pav.delete()
            log_request(request, f"Product attribute value {pk} deleted", "info",
                        "Product attribute value deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product attribute value deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)

        except models.ProductAttributeValue.DoesNotExist:
            log_request(request, f"Product attribute value {pk} deletion failed", "warning",
                        "Product attribute value not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute value not found",
                "data": {
                    "product_attribute_value": f"Product attribute value not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product attribute value {pk} deletion failed", "error",
                        f"Product attribute value deletion failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttributeSpecificValuesListView(APIView): 
    def get(self, request,pk):
        try:
            
            product_attribute = models.ProductAttribute.objects.get(pk=pk)
            attribute_values = models.ProductAttributeValue.objects.filter(attribute=product_attribute)

            serializer = serializers.ProductAttributeValueSerializer(attribute_values, many=True)
            log_request(
                request,
                f"Product attribute {pk} specific values fetched",
                "info",
                "Product specific attribute values fetched successfully",
                response_status_code=status.HTTP_200_OK
            )
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product specific attribute values fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product attribute {pk} specific values fetch failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found",
                "data": {
                    "product": f"Product not found with id {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except models.ProductAttribute.DoesNotExist:
            log_request(
                request,
                f"Product attribute id {pk} specific values fetch failed",
                "warning",
                "Product attribute not found for this product",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product attribute not found for this product",
                "data": {
                    "attribute": f"Product attribute not found with ID {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                f"Product  attribute {pk} specific values fetch failed",
                "error",
                f"Server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": { "server_error": [str(e)] }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ProductVariantView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            variants = models.ProductVariant.objects.select_related('product').all()
            paginator = CustomPageNumberPagination()
            variants = paginator.paginate_queryset(variants, request, view=self)
            serializer = serializers.ProductVariantSerializerView(variants, many=True)
            log_request(request, "Product variants fetched", "info", "Product variants fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product variants fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product variant fetch failed", "error", "Product variant fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Product variant fetch failed due to server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = serializers.ProductVariantSerializer(data=request.data)
            if serializer.is_valid():
                variant = serializer.save()
                log_request(request, "Product variant created", "info", f"Product variant created successfully by this {variant.product.title}", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Product variant created successfully",
                    "data": {
                        "id": variant.id,
                        "name": variant.variant_name,
                        "price": variant.price,
                        "product": variant.product.title,
                    }
                }, status=status.HTTP_201_CREATED)
            log_request(request, "Product variant creation failed", "warning", "Validation failed for product variant creation", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "fail",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product variant creation error", "error", "Product variant creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product variant creation failed due to server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            variant = models.ProductVariant.objects.select_related('product').get(pk=pk)
            serializer = serializers.ProductVariantDetailSerializerView(variant)
            log_request(request, f"Product variant {pk} fetched", "info", "Product variant fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product variant fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except models.ProductVariant.DoesNotExist:
            log_request(request, f"Product variant {pk} fetch failed", "warning", "Product variant not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product variant not found",
                "data": {"product_variant": f"Product variant not found with id {pk}"}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant {pk} fetch failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            variant = models.ProductVariant.objects.get(pk=pk)
            serializer = serializers.ProductVariantSerializer(variant, data=request.data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, f"Product variant {pk} updated", "info", "Product variant updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Product variant updated successfully",
                    "data": serializers.ProductVariantSerializerView(instance).data
                }, status=status.HTTP_200_OK)
            log_request(request, f"Product variant {pk} update failed", "warning", "Validation failed for product variant update", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Product variant update failed due to validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except models.ProductVariant.DoesNotExist:
            log_request(request, f"Product variant {pk} update failed", "warning", "Product variant not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product variant not found",
                "data": {
                    "product_variant": f"Product variant not found with id {pk}"
                }
            
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant {pk} update failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            variant = models.ProductVariant.objects.get(pk=pk)
            variant.delete()
            log_request(request, f"Product variant {pk} deleted", "info", "Product variant deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product variant deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.ProductVariant.DoesNotExist:
            log_request(request, f"Product variant {pk} delete failed", "warning", "Product variant not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product variant not found",
                "data":{
                    "product_variant": f"Product variant not found with id {pk}"
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant {pk} delete failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Product variant delete failed due to server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductVariantAttributeView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = serializers.ProductVariantAttributeCreateSerializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save()
                log_request(request, "Product variant attribute created", "info", "Product variant attribute created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Product variant attribute created successfully",
                    "data": {
                        "id": instance.id,
                        "variant": instance.variant.variant_name,
                        "attribute": instance.attribute.name,
                        "value": instance.value.value
                    }
                }, status=status.HTTP_201_CREATED)
            log_request(request, "Product variant attribute creation failed", "warning", "Validation failed for product variant attribute creation", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "product variant creation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product variant attribute creation error", "error", "Product variant attribute creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Product variant attribute creation failed due to server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            variant_id = request.GET.get('variant')
            qs = models.ProductVariantAttribute.objects.select_related('variant', 'attribute', 'value').all()
            if variant_id:
                qs = qs.filter(variant_id=variant_id)
            paginator = CustomPageNumberPagination()
            paged = paginator.paginate_queryset(qs, request, view=self)
            serializer = serializers.ProductVariantAttributeSerializerView(paged, many=True)
            log_request(request, "Product variant attributes fetched", "info", "Product variant attributes fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product variant attributes fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product variant attribute fetch failed", "error", "Product variant attribute fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Product variant attribute fetch failed due to server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductVariantAttributeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            instance = models.ProductVariantAttribute.objects.select_related('variant', 'attribute', 'value').get(pk=pk)
            serializer = serializers.ProductVariantAttributeSerializerView(instance)
            log_request(request, f"Product variant attribute {pk} fetched", "info", "Product variant attribute fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product variant attribute fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except models.ProductVariantAttribute.DoesNotExist:
            log_request(request, f"Product variant attribute {pk} fetch failed", "warning", "Product variant attribute not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product variant attribute not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant attribute {pk} fetch failed", "error", "Server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            instance = models.ProductVariantAttribute.objects.get(pk=pk)
            serializer = serializers.ProductVariantAttributeCreateSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                obj = serializer.save()
                log_request(request, f"Product variant attribute {pk} updated", "info", "Product variant attribute updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Product variant attribute updated successfully",
                    "data": serializers.ProductVariantAttributeSerializerView(obj).data
                }, status=status.HTTP_200_OK)
            log_request(request, f"Product variant attribute {pk} update failed", "warning", "Validation failed", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "fail",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except models.ProductVariantAttribute.DoesNotExist:
            log_request(request, f"Product variant attribute {pk} update failed", "warning", "Not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product variant attribute not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant attribute {pk} update failed", "error", "Server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            instance = models.ProductVariantAttribute.objects.get(pk=pk)
            instance.delete()
            log_request(request, f"Product variant attribute {pk} deleted", "info", "Product variant attribute deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product variant attribute deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.ProductVariantAttribute.DoesNotExist:
            log_request(request, f"Product variant attribute {pk} delete failed", "warning", "Not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Product variant attribute not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product variant attribute {pk} delete failed", "error", "Server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class SingleProductDetailInformationView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        # fetch associate product details,product_attribute_detail,product_attributes_values,ProductImages,productVariantAttribute
        try:
            product = models.Product.objects.select_related(
                'store', 'category', 'brand'
            ).prefetch_related(
                'images',
                'attributes__values', # Prefetch attributes and their values
                'variants__variant_attrs__attribute', # Prefetch variants, their attributes, and the attribute details
                'variants__variant_attrs__value' # Prefetch variants, their attributes, and the attribute value details
            ).get(slug=slug)

            # Serialize the product details
            serializer = serializers.SingleProductDetailInformationSerializerView(product)
            log_request(request, f"Product {slug} information fetched", "info", "Product  information fetched successfully", response_status_code=status.HTTP_200_OK)

            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product information fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except models.Product.DoesNotExist:
            log_request(request, f"Product {slug} information fetch failed", "warning", "Product not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product {slug} information fetch failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      
class ProductAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            # Fetch all product analytics
            product_analytics = models.ProductAnalytics.objects.select_related('product').all()
            
            # Apply pagination
            paginator = CustomPageNumberPagination()
            paged_analytics = paginator.paginate_queryset(product_analytics, request, view=self)
            
            # Serialize the data
            # You might need a dedicated serializer for ProductAnalytics if you want to customize the output
            # For now, let's use a basic serializer or just return the raw data
            serialized_data = []
            for pa in paged_analytics:
                serialized_data.append({
                    "id": pa.id,
                    "product_id": pa.product.id,
                    "product_title": pa.product.title,
                    "date": pa.date,
                    "views": pa.views,
                    # "add_to_cart": pa.add_to_cart,
                    # "wishlist": pa.wishlist,
                    # "sales_count": pa.sales_count,
                    # "revenue": pa.revenue,
                })

            log_request(
                request,
                "All product analytics fetched",
                "info",
                "All product analytics fetched successfully",
                response_status_code=status.HTTP_200_OK
            )

            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "All product analytics fetched successfully",
                "data": serialized_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Product analytics fetch failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SingleProductAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, slug):
        try:
            product = models.Product.objects.get(slug=slug)

            # Basic analytics: view count
            analytics_data = {
                "product_id": product.id,
                "product_title": product.title,
                "view_count": product.view_count,
                # Add more analytics data here as needed, e.g.,
                # "total_sales": product.order_items.aggregate(total_sales=Sum('quantity'))['total_sales'],
                # "average_rating": product.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'],
            }

            log_request(
                request,
                f"Product {slug} analytics fetched",
                "info",
                "Product analytics fetched successfully",
                response_status_code=status.HTTP_200_OK
            )

            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product analytics fetched successfully",
                "data": analytics_data
            }, status=status.HTTP_200_OK)

        except models.Product.DoesNotExist:
            log_request(
                request,
                f"Product {slug} analytics fetch failed",
                "warning",
                "Product not found",
                response_status_code=status.HTTP_404_NOT_FOUND
            )
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, f"Product {slug} analytics fetch failed", "error", f"Server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            

class LatestProductsView(APIView):
    """
    Get latest 15 products with pagination
    """
    def get(self, request):
        try:
            # Filter only published products
            queryset = models.Product.objects.select_related('brand','category','store').filter(
                status="published"
            ).order_by("-created_at")[:16]
                
            serializer = serializers.ProductSerializerView(queryset, many=True)
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Latest products fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Failed to fetch latest products",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BestSellingProductsView(APIView):
    """
    Get 15 best selling products based on actual order data
    """
    def get(self, request):
        try:
            
            # Aggregate total quantity sold for each product
            product_sales = OrderItem.objects.filter(
                order__payment_status='paid',  # Only paid orders
                order__status__in=['confirmed', 'completed', 'delivered'] 
            ).values('product_id').annotate(
                total_quantity_sold=Sum('quantity')
            ).order_by('-total_quantity_sold')
            
            # Get product IDs with sales data
            product_ids = [item['product_id'] for item in product_sales if item['product_id']]
            
            # Get product objects
            products_by_sales = models.Product.objects.filter(
                id__in=product_ids,
                status="published"
            ).in_bulk(product_ids)
            
            # Create ordered list based on sales
            ordered_products = []
            for pid in product_ids:
                if pid in products_by_sales:
                    ordered_products.append(products_by_sales[pid])
            
            # If there are not enough products with sales data,
            # add more published products
            if len(ordered_products) < 16:
                additional_products = models.Product.objects.filter(
                    status="published"
                ).exclude(
                    id__in=product_ids
                ).order_by("-created_at")[:16 - len(ordered_products)]
                ordered_products.extend(list(additional_products))
            
            # Apply pagination with page size 15
            paginator = CustomPageNumberPagination()
            paginator.page_size = 16
            
            # Paginate the ordered_products list
            paginated_products = paginator.paginate_queryset(ordered_products, request, view=self)
            
            # Create a custom serializer response with sales data
            product_list = []
            for product in paginated_products:
                # Find sales count for this product
                sales_data = next(
                    (item for item in product_sales if item['product_id'] == product.id), 
                    {'total_quantity_sold': 0}
                )
                
                # Get basic product data
                product_data = serializers.ProductSerializerView(product).data
                # Add sales count
                product_data['total_sales'] = sales_data['total_quantity_sold']
                product_list.append(product_data)
            
            # Return paginated response
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Best selling products fetched successfully",
                "data": product_list
            })
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Failed to fetch best selling products",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            


class TopFiveCategoriesProductView(APIView):
    """
    Get top 5 categories with their products (optimized)
    """
    
    
    def get(self, request):
        try:
            # SINGLE QUERY SOLUTION: Get all required data in one optimized query            
            # Subquery to get latest product IDs for each category
            # latest_product_subquery = models.Product.objects.filter(
            #     category_id=OuterRef('pk'),
            #     status="published"
            # ).order_by('-created_at').values('id')[:10]
            
            # Get categories with products in a single query
            categories = Category.objects.filter(
                is_active=True
            ).order_by('display_order')[:5].prefetch_related(
                Prefetch(
                    'products',
                    queryset=models.Product.objects.filter(
                        status="published"
                    ).select_related(
                        'store', 'brand', 'category'
                    ).only(
                        'id', 'slug', 'title', 'type', 'description',
                        'base_price', 'main_image', 'stock', 'is_featured',
                        'status', 'store_id', 'brand_id', 'category_id'
                    ).order_by('-created_at')[:10],
                    to_attr='category_products'
                )
            ).annotate(
                products_count=Count('products', filter=Q(products__status="published"))
            )
            
            # Prepare response data
            response_data = []
            
            for category in categories:
                # Get products directly from prefetched data
                category_products = getattr(category, 'category_products', [])
                
                # Serialize products
                product_serializer = serializers.ProductSerializerView(
                    category_products,
                    many=True,
                )
                
                category_data = {
                    "category_id": category.id,
                    "category_name": category.name,
                    "category_slug": category.slug,
                    "display_order": category.display_order,
                    "products_count": getattr(category, 'products_count', len(category_products)),
                    "products": product_serializer.data
                }
                
                response_data.append(category_data)
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Categories with products fetched successfully",
                "data": response_data
            })
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Failed to fetch categories with products",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)