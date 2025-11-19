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
                "status": "error",
                "message": "Store fetch failed due to server error",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class  OwnStoreView(APIView):
    permission_classes = [IsAuthenticated]
    
    
    def get(self,request):
        try:
            user = request.user
            # Collect stores related to the authenticated user
            stores_qs = models.Store.objects.none()

            # Vendor account -> stores where vendor matches
            try:
                if hasattr(user, 'vendor_profile'):
                    stores_qs = stores_qs | models.Store.objects.filter(vendor__user=user)
            except Exception:
                # defensive: ignore if vendor_profile relation not present
                pass

            # Store owner account -> stores where store_owner matches
            try:
                if hasattr(user, 'store_owner_profile'):
                    stores_qs = stores_qs | models.Store.objects.filter(store_owner__user=user)
            except Exception:
                pass

            if not stores_qs.exists():
                log_request(request, f"Own store {user.email} fetch", "info", "No stores found for user", response_status_code=status.HTTP_404_NOT_FOUND)
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "fail",
                    "message": "No stores found for the authenticated user",
                    "data": []
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = serializers.StoreSerializerForView(stores_qs.distinct(), many=True)
            log_request(request, f" {user.email} own stores fetched", "info", " stores fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Stores fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
            
        except models.Store.DoesNotExist:
            log_request(request, "Vendor store fetch failed", "warning", "Store not found for user", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "fail",
                "message": "Store not found for the authenticated user",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Vendor store fetch error", "error", "Error fetching vendor store(s)", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Error fetching store(s) due to server error",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

