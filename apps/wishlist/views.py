# apps/wishlist/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.shortcuts import get_object_or_404


from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistListSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer
)

logger = logging.getLogger("myapp")



class WishlistView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            wishlists = Wishlist.objects.all()
            serializer = WishlistListSerializer(wishlists, many=True)

            return Response({
                "code": 200,
                "message": "Wishlists fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=200)

        except Exception as e:
            logger.exception(str(e))
            return Response({"code": 500, "status": "failed", "message": "Server error", "errors": {"server": [str(e)]}}, status=500)




class WishlistItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # ---------------------------
    # Utility
    # ---------------------------
    def _get_default_wishlist(self, user):
        wishlist, _ = Wishlist.objects.get_or_create(
            user=user,
            is_default=True,
            defaults={"name": "My Wishlist"}
        )
        return wishlist

    # ---------------------------
    # POST → Add item
    # ---------------------------
    def post(self, request):
        try:
            wishlist = self._get_default_wishlist(request.user)

            serializer = WishlistItemCreateSerializer(
                data=request.data,
                context={"wishlist": wishlist}
            )

            if serializer.is_valid():
                item = serializer.save()

                return Response(
                    {
                        "code": status.HTTP_201_CREATED,
                        "status": "success",
                        "message": "Item added to wishlist",
                        "data": {
                            "id": item.id,
                            "product": item.product.id,
                            "variant": item.variant.id if item.variant else None,
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "failed",
                        "message": "Invalid data",
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
        except Exception as e:
            logger.exception("Wishlist add failed")
            return Response(
                {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": "failed",
                    "message": "Server error",
                    "errors": {"server": [str(e)]},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            items = wishlist.items.select_related('product', 'variant').filter(wishlist=wishlist)
            serializer = WishlistItemSerializer(items, many=True)

            return Response({
                "code": 200,
                "message": "Wishlist items fetched",
                "status": "success",
                "data": serializer.data
            }, status=200)
        except Wishlist.DoesNotExist:
            return Response({"code": 404
                             ,"status": "failed",
                             "message": "Wish list item  not found"
                             ,"errors": {"wishlist": ["Wishlist not found "]}
                             }, status=404)
        except Exception as e:
            logger.exception(str(e))

            return Response({"code": 500, 
                             "message": "Server error",
                             "status": "failed",
                             "errors": {"server": [str(e)]},
                             
                             }, status=500)



class WishlistItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = WishlistItem.objects.get(wishlist__user=request.user, id=item_id)
            item.delete()
            return Response({
                "code": 204,
                "message": "Item deleted from wishlist",
                "status": "success"
            }, status=204)
        except WishlistItem.DoesNotExist:
            return Response({"code": 404,
                             "status": "failed",
                             "message": "This item not found in wishlist",
                             "errors": {"wishlist": ["This item not found in wishlist"]}
                             }, status=404)
        except Exception as e:
            logger.exception(str(e))
            return Response({"code": 500,
                             "status": "failed",
                             "message": "Server error",
                             "errors": {"server": [str(e)]}
                             }, status=500)

