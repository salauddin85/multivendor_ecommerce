from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
import logging

from .models import Coupon, CouponUsage
from .serializers import (
    CouponCreateSerializer,
    CouponSerializerView,
    CouponUsageSerializerView
    ,CouponDetailSerializer
)
from apps.activity_log.utils.functions import log_request
from config.utils.pagination import CustomPageNumberPagination

logger = logging.getLogger("myapp")



class CouponView(APIView):

    def post(self, request):
        try:
            serializer = CouponCreateSerializer(data=request.data)
            if serializer.is_valid():
                coupon = serializer.save()
                log_request(request, "Coupon created", "info", "Coupon created successfully",
                            response_status_code=status.HTTP_201_CREATED)

                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Coupon created successfully",
                    "data": {
                        "id": coupon.id,
                        "code": coupon.code,
                        "type": coupon.type
                    }
                }, status=status.HTTP_201_CREATED)

            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            coupons = Coupon.objects.filter(status='active').order_by('-created_at')
            paginator = CustomPageNumberPagination()
            paged = paginator.paginate_queryset(coupons, request, view=self)
            serializer = CouponSerializerView(paged, many=True)
            log_request(request, "Fetched coupons", "info", "Coupons fetched successfully",
                        response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Coupons fetched successfully",
                "data": serializer.data
            })

        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CouponUsageView(APIView):

    def get(self, request):
        try:
            usages = CouponUsage.objects.select_related(
                'coupon', 'user', 'store'
            ).order_by('-created_at')

            paginator = CustomPageNumberPagination()
            paged = paginator.paginate_queryset(usages, request, view=self)
            serializer = CouponUsageSerializerView(paged, many=True)
            log_request(request, "Fetched coupon usages", "info", "Coupon usages fetched successfully",
                        response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Coupon usages fetched successfully",
                "data": serializer.data
            })

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Error fetching coupon usages", "error", "Server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CouponDetailView(APIView):

    def get(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
            serializer = CouponDetailSerializer(coupon)

            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Coupon fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Coupon.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Coupon not found",
                "errors": {"coupon": ["Coupon with the given ID does not exist"]}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def patch(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
            serializer = CouponCreateSerializer(coupon, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Coupon updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
        except Coupon.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Coupon not found",
                "errors": {"coupon": ["Coupon with the given ID does not exist"]}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
            coupon.status = 'inactive'
            coupon.save()
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Coupon deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except Coupon.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Coupon not found",
                "errors": {"coupon": ["Coupon with the given ID does not exist"]}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
     