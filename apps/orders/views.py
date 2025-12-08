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
from django.db import transaction


class ShippingAddressView(APIView):
    permission_classes = [IsAuthenticated]

    # Create Shipping Address
    def post(self, request):
        try:
            serializer = serializers.ShippingAddressSerializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save(user=request.user)

                return Response(
                    {
                        "code": status.HTTP_201_CREATED,
                        "status": "success",
                        "message": "Shipping address created successfully.",
                        "data": {
                            "id": instance.id,
                            "user": instance.user.email,
                            "name": instance.name,
                            "phone": instance.phone,
                            "address_line": instance.address_line,
                        
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Invalid data provided.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception(str(e))
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "An error occurred while creating shipping address.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # Get All Shipping Addresses
    def get(self, request):
        try:
            shipping_addresses = models.ShippingAddress.objects.filter(user = request.user)
            serializer = serializers.ShippingAddressSerializerForView(shipping_addresses, many=True)

            return Response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Shipping addresses retrieved successfully.",
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
                    "message": "An error occurred while retrieving shipping addresses.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ShippingAddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            
            shipping_address = models.ShippingAddress.objects.get(pk=pk, user=request.user)
            serializer = serializers.ShippingAddressSerializerForView(shipping_address)

            return Response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Shipping address retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except models.ShippingAddress.DoesNotExist:
            return Response(
                {
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Shipping address not found.",
                    "errors": {
                        "shipping_address_id": f"Shipping address not found for id {pk}."
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("An error occurred while retrieving shipping address.")
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "An error occurred while retrieving shipping address.",
                    "errors": {
                        "server_error": [str(e)]
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def delete(self, request, pk):
        try:
            try:
                shipping_address = models.ShippingAddress.objects.get(pk=pk, user=request.user)
            except models.ShippingAddress.DoesNotExist:
                return Response(
                    {
                        "code": status.HTTP_404_NOT_FOUND,
                        "status": "failed",
                        "message": "Shipping address not found.",
                        "errors": {
                            "shipping_address_id": "Shipping address not found."
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            shipping_address.delete()

            return Response(
                {
                    "code": status.HTTP_204_NO_CONTENT,
                    "status": "success",
                    "message": "Shipping address deleted successfully.",
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            logger.exception("Error deleting shipping address.")
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "An error occurred while deleting shipping address.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    

class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            serializer = serializers.OrderSerializer(data=request.data, context={"request": request})

            if serializer.is_valid():
                order = serializer.save()

                return Response(
                    {
                        "code": status.HTTP_201_CREATED,
                        "status": "success",
                        "message": "Order created successfully.",
                        "data": {
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "total_amount": order.total_amount,
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "order creation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception(str(e))
            transaction.set_rollback(True)
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "Order creation failed.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    
    def get(self, request):
        try:
            paginator = CustomPageNumberPagination()
            # Only logged-in user orders
            orders = models.Order.objects.filter(user=request.user).order_by("-created_at")

            # Paginate
            paginated_orders = paginator.paginate_queryset(orders, request)

            serializer = serializers.OrderSerializerView(
                paginated_orders, many=True
            )

            return paginator.get_paginated_response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Orders retrieved successfully.",
                    "data": serializer.data,
                }
            )

        except Exception as e:
            logger.exception(str(e))
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "An error occurred while retrieving orders.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

            

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = models.Order.objects.select_related('user','shipping_address','parent').get(pk=pk, user=request.user)
            serializer = serializers.OrderDetailSerializerView(order)
            return Response(  {
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Order retrieved successfully.",
                "data": serializer.data,
            } , status=status.HTTP_200_OK)
        except models.Order.DoesNotExist:
            return Response(
                {
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Order not found.",
                    "errors":{
                        "order_id": [f"Order not found with id {pk}"]
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "An error occurred while retrieving order.",
                "errors": {"server_error": [str(e)]},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                         
            
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            orders = models.Order.objects.select_related('user','shipping_address','parent').filter(user=request.user)
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(orders, request)
            serializer = serializers.OrderSerializerView(result_page, many=True)

            return paginator.get_paginated_response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Orders retrieved successfully.",
                    "data": serializer.data,
                }
            )

        except Exception as e:
            logger.exception(str(e))
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "An error occurred while retrieving orders.",
                    "errors": {"server_error": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            

class StoreOrderListView(APIView):
    
    def get(self, request, store_id):
        try:
            orders = models.Order.objects.filter(store_id=store_id)
            serializer = serializers.OrderSerializerView(orders, many=True)
            return Response(
                {
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Orders retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        
        except models.Order.DoesNotExist:
            return Response(
                {
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Order not found by store id.",
                    "errors":{
                        "store_id": [f"Order not found with store id {store_id}"]
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
                    
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "An error occurred while retrieving orders.",
                "errors": {"server_error": [str(e)]},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
            