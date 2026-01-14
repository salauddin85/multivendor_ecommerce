from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import models
from . import serializers
from apps.activity_log.utils.functions import log_request
import logging
logger = logging.getLogger("myapp")
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from config.utils.pagination import CustomPageNumberPagination
from django.db.models import Q



class StoresView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    
    def get(self, request):
        
        try:
            stores = models.Store.objects.all()
            paginator = CustomPageNumberPagination()
            stores = paginator.paginate_queryset(stores, request)
            serializer = serializers.StoreSerializerForView(stores, many=True)
            log_request(request, "All stores fetched", "info", "All stores fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "All stores fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Store fetch failed", "error","Store fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)    
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Store fetch failed due to server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OwnStoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        stores_qs = models.Store.objects.select_related('vendor', 'store_owner').filter(
            Q(vendor__user=user) | Q(store_owner__user=user)
        ).distinct()

        # check if empty using the same queryset (exists() will hit DB once)
        if not stores_qs.exists():
             return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "No stores found",
                "data": []
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.StoreSerializerForView(stores_qs, many=True)
        
        return Response({
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Stores fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        try:
           
            user = request.user
            store_qs = models.Store.objects.filter(
                Q(vendor__user=user) | Q(store_owner__user=user)
            ).distinct()
            if not store_qs.exists():
                log_request(request, "Store update failed", "warning", "No store found for the user", response_status_code=status.HTTP_404_NOT_FOUND)
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "No store found for the user",
                    "data": []
                }, status=status.HTTP_404_NOT_FOUND)
            serializer = serializers.StoreUpdateSerializer(data=request.data, instance=store_qs.first(), partial=True)
            if serializer.is_valid():
                store = serializer.save()
                log_request(request, "Store updated", "info", "Store updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Store updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                log_request(request, "Store update failed", "warning", "Invalid data for store update", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Invalid data",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Store update error", "error", "Error updating store", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Store update failed due to server error",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    

class CommissionRatesView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    
    def post(self, request):
        try:
            serializer = serializers.CommissionRateSerializer(data=request.data)
            if serializer.is_valid():
                commission_rate = serializer.save()
                log_request(request, "Commission rate created", "info", "Commission rate created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Commission rate created successfully",
                    "data": serializers.CommissionRateSerializer(commission_rate).data
                }, status=status.HTTP_201_CREATED)
            else:
                log_request(request, "Commission rate creation failed", "warning", "Invalid data for commission rate", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "fail",
                    "message": "Invalid data",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Commission rate creation error", "error", "Error creating commission rate", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Error creating commission rate due to server error",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
    def get(self, request):
        try:
            commission_rates = models.CommissionRate.objects.all()
            serializer = serializers.CommissionRateSerializer(commission_rates, many=True)
            log_request(request, "Commission rates fetched", "info", "Commission rates fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Commission rates fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Commission rates fetch error", "error", "Error fetching commission rates", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Error fetching commission rates due to server error",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)