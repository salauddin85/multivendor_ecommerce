from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from . import serializers
from apps.activity_log.utils.functions import log_request
import logging
logger = logging.getLogger("myapp")
from django.db import transaction
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from config.utils.pagination import CustomPageNumberPagination
from apps.products.models import (Product,ProductVariant,ProductVariantAttribute,
                                  ProductAttribute,ProductAttributeValue)
from apps.products.serializers import (ProductSerializerView,ProductVariantSerializerView,
                                       ProductAttributeSerializerForView,
                                       ProductAttributeValueSerializer)

from apps.stores.models import Store
from apps.authentication.models import Vendor,Staff
#  ---------------------------------------------------------------------------


# class VendorProfileUpdateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def patch(self, request):
#         try:
#             with transaction.atomic():
#                 vendor = request.user.vendor

#                 serializer = serializers.VendorProfileSerializer(
#                     vendor,
#                     data=request.data,
#                     partial=True
#                 )

#                 if serializer.is_valid():
#                     instance = serializer.save()

#                     log_request(
#                         request,
#                         "Vendor profile updated",
#                         "info",
#                         "Vendor profile updated successfully",
#                         response_status_code=status.HTTP_200_OK
#                     )

#                     return Response({
#                         "code": status.HTTP_200_OK,
#                         "status": "success",
#                         "message": "Vendor profile updated successfully",
#                         "data": serializer.data
#                     }, status=status.HTTP_200_OK)

#                 log_request(
#                     request,
#                     "Vendor profile update failed",
#                     "warning",
#                     "Vendor profile update failed due to invalid data",
#                     response_status_code=status.HTTP_400_BAD_REQUEST
#                 )

#                 return Response({
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "status": "failed",
#                     "message": "Vendor profile update failed due to invalid data",
#                     "errors": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         except AttributeError:
#             log_request(
#                 request,
#                 "Vendor profile update failed",
#                 "warning",
#                 "Vendor profile not found",
#                 response_status_code=status.HTTP_404_NOT_FOUND
#             )

#             return Response({
#                 "code": status.HTTP_404_NOT_FOUND,
#                 "status": "failed",
#                 "message": "Vendor profile not found",
#                 "data": {
#                     "vendor": "Vendor profile does not exist for this user"
#                 }
#             }, status=status.HTTP_404_NOT_FOUND)

#         except Exception as e:
#             logger.exception(str(e))

#             log_request(
#                 request,
#                 "Vendor profile update failed",
#                 "error",
#                 f"Vendor profile update failed due to server error: {str(e)}",
#                 response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#             return Response({
#                 "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 "status": "failed",
#                 "message": "Internal server error",
#                 "errors": {
#                     "server_error": [str(e)]
#                 }
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VendorAllProducts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            products = Product.objects.filter(store__vendor__user=request.user)
            pagination = CustomPageNumberPagination()
            paginated_products = pagination.paginate_queryset(products, request)
            serializer = ProductSerializerView(paginated_products, many=True)
            return pagination.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Products retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            



class VendorProductVariantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
           
            product_variants = ProductVariant.objects.filter(
                product__store__vendor__user=request.user
            ).select_related("product")

            pagination = CustomPageNumberPagination()
            paginated_variants = pagination.paginate_queryset(
                product_variants, request
            )

            serializer = ProductVariantSerializerView(
                paginated_variants, many=True
            )

            # ==========================
            # RESPONSE (CONSISTENT FORMAT)
            # ==========================
            return pagination.get_paginated_response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Product variants retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
                   
        except Exception as e:
            logger.exception(str(e))
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "Internal server error",
                    "errors": {
                        "server_error": [str(e)]
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

      
class VendorProductAttributeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            product_attributes = ProductAttribute.objects.filter(
                product__store__vendor__user=request.user
            ).select_related("product")

            pagination = CustomPageNumberPagination()
            paginated_attributes = pagination.paginate_queryset(
                product_attributes, request
            )

            serializer = ProductAttributeSerializerForView(
                paginated_attributes, many=True
            )

            log_request(
                request,
                "Vendor product attributes fetched",
                "info",
                "Vendor product attributes fetched successfully",
                response_status_code=status.HTTP_200_OK
            )

            return pagination.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Vendor product attributes fetched successfully",
                "data": serializer.data
            })

        except Exception as e:
            logger.exception(str(e))

            log_request(
                request,
                "Vendor product attributes fetch failed",
                "error",
                f"Failed to fetch vendor product attributes due to server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VendorProductAttributeValuesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # 1. Attribute ownership check (Vendor security)
            product_attribute = ProductAttribute.objects.get(
                pk=pk,
                product__store__vendor__user=request.user
            )

            # 2. Get ALL values for this attribute
            attribute_values = ProductAttributeValue.objects.filter(
                attribute=product_attribute
            ).select_related("attribute")

            serializer = ProductAttributeValueSerializer(
                attribute_values,
                many=True
            )

            log_request(
                request,
                f"Vendor product attribute values fetched for attribute {pk}",
                "info",
                "Vendor product attribute values fetched successfully",
                response_status_code=status.HTTP_200_OK
            )

            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product attribute values fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except ProductAttribute.DoesNotExist:
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
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class VendorOwnProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            vendor = Vendor.objects.select_related('user').filter(user=user).first()
            serializer = serializers.VendorProfileSerializer(vendor)
            log_request(
                request,
                "Vendor profile retrieved",
                "info",
                "Vendor profile retrieved successfully",
                response_status_code=status.HTTP_200_OK
            )
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Vendor profile retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                "Vendor profile retrieval failed",
                "error",
                f"Vendor profile retrieval failed due to server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class VendorAllOwnStaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            staff_members = Staff.objects.select_related('user').filter(vendor__user=user)
            serializer = serializers.StaffSerializerForView(staff_members, many=True)
            log_request(
                request,
                "Vendor staff members retrieved",
                "info",
                "Vendor staff members retrieved successfully",
                response_status_code=status.HTTP_200_OK
            )
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Vendor staff members retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                "Vendor staff members retrieval failed",
                "error",
                f"Vendor staff members retrieval failed due to server error: {str(e)}",
                response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Internal server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)