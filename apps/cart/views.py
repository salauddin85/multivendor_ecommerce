from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum
from .models import Cart, CartItem
from apps.products.models import Product, ProductVariant
from .serializers import (
    CartSerializer, CartItemSerializer,
    CartAddProductSerializer, CartItemUpdateSerializer
)
from .services.cart_manage import get_or_create_cart





class CartView(APIView):

    def get(self, request):
        """ Retrieve Auth + Guest cart """
        try:
            cart = get_or_create_cart(request)
            return Response({
                "code": 200,
                "status": "success",
                "message": "Cart retrieved successfully",
                "data": CartSerializer(cart).data
            }, status=200)

        except Exception as e:
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Failed to retrieve cart",
                "errors": {"server_error": [str(e)]}
            }, status=500)

    @transaction.atomic
    def post(self, request):
        """ Add product or variant to cart """
        try:
            serializer = CartAddProductSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=400)

            data = serializer.validated_data

            product = data["product"]
            variant = data.get("variant", None)
            quantity = data["quantity"]

            # --- Product Must Be Published ---
            if product.status != "published":
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Product is not published",
                    "errors": {"product": ["Product is not available for sale"]}
                }, status=400)

            # --- Variant Must Belong to Product ---
            if variant and variant.product_id != product.id:
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Invalid variant",
                    "errors": {"variant": ["Variant does not belong to this product"]}
                }, status=400)

            # --- Stock Check ---
            stock = variant.stock if variant else product.stock

            if quantity > stock:
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Insufficient stock",
                    "errors": {"quantity": [f"Only {stock} available in stock"]}
                }, status=400)

            # --- Create or Get Cart ---
            cart = get_or_create_cart(request)

            # --- Check Existing Cart Item ---
            item = CartItem.objects.filter(
                cart=cart,
                product=product,
                variant=variant
            ).first()

            # --- Calculate Price ---
            if variant:
                price = variant.discount_price or variant.price
            else:
                price = product.base_price

            # --- Update Existing Item ---
            if item:
                new_qty = item.quantity + quantity

                if new_qty > stock:
                    return Response({
                        "code": 400,
                        "status": "failed",
                        "message": "Stock limit exceeded",
                        "errors": {"quantity": [f"Only {stock} available"]}
                    }, status=400)

                item.quantity = new_qty
                item.subtotal = price * new_qty
                item.save()

            else:
                # --- Create New Cart Item ---
                item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    price=price,
                    subtotal=price * quantity
                )

            # --- Update Cart Total ---
            cart.total_amount = cart.items.aggregate(
                total=Sum("subtotal")
            )["total"] or 0
            cart.save()

            return Response({
                "code": 201,
                "status": "success",
                "message": "Item added to cart successfully",
                "data": CartItemSerializer(item).data
            }, status=201)

        except Exception as e:
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Failed to add item",
                "errors": {"server_error": [str(e)]}
            }, status=500)


class CartItemUpdateDeleteView(APIView):

    @transaction.atomic
    def patch(self, request, item_id):
        try:
            serializer = CartItemUpdateSerializer(data=request.data)
            if serializer.is_valid():
                
                qty = serializer.validated_data['quantity']

                cart = get_or_create_cart(request)

                item = CartItem.objects.get(id=item_id, cart=cart)

                stock = item.variant.stock if item.variant else item.product.stock
                if qty > stock:
                    return Response({
                        "code": 400,
                        "status": "failed",
                        "message": f"Only {stock} in stock"
                    }, status=400)

                item.quantity = qty
                item.subtotal = item.price * qty
                item.save()

                # Update total
                cart.total_amount = cart.items.aggregate(total=Sum("subtotal"))['total'] or 0
                cart.save()

                return Response({
                    "code": 200,
                    "status": "success",
                    "message": "Cart item updated",
                    "data": CartItemSerializer(item).data
                }, status=200)
            else:
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=400)

        except CartItem.DoesNotExist:
            return Response({
                "code": 404,
                "status": "failed",
                "message": "Item not found",
                "errors": {
                    "item_id": [f"Item not found with id {item_id}"]
                }
            }, status=404)

        except Exception as e:
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Failed to update item",
                "errors": {"server_error": [str(e)]}
            }, status=500)



    @transaction.atomic
    def delete(self, request, item_id):
        try:
            cart = get_or_create_cart(request)
            item = CartItem.objects.get(id=item_id, cart=cart)

            item.delete()

            cart.total_amount = cart.items.aggregate(total=Sum("subtotal"))['total'] or 0
            cart.save()

            return Response({
                "code": 200,
                "status": "success",
                "message": "Item removed",
                "data": {"item_id": item_id}
            }, status=200)

        except CartItem.DoesNotExist:
            return Response({
                "code": 404,
                "status": "failed",
                "message": "Item not found",
                'errors': {
                    "item_id": [f"Item not found with id {item_id}"]
                }
                
                
            }, status=404)
        
        except Exception as e:
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Failed to remove item",
                "errors": {"server_error": [str(e)]}
            }, status=500)




class CartClearView(APIView):

    @transaction.atomic
    def delete(self, request):
        try:
            cart = get_or_create_cart(request)

            cart.items.all().delete()
            cart.total_amount = 0.00
            cart.session_id = None
            cart.save()

            return Response({
                "code": 200,
                "status": "success",
                "message": "Cart cleared successfully",
                
            })

        except Exception as e:
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Failed to clear cart",
                "errors": {"server_error": [str(e)]}
            }, status=500)
