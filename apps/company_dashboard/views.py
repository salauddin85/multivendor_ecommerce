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
from apps.authentication.models import Vendor,Staff,StoreOwner

# TODO(permission): Add IsCompanyUser permission later


class CompanyOwnProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            company = StoreOwner.objects.select_related('user').filter(user=user).first()
            serializer = serializers.CompanyProfileSerializer(company)
            log_request(
                request,
                "Company profile retrieved",
                "info",
                "Company profile retrieved successfully",
                response_status_code=status.HTTP_200_OK
            )
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Company profile retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(
                request,
                "Company profile retrieval failed",
                "error",
                f"Company profile retrieval failed due to server error: {str(e)}",
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
          