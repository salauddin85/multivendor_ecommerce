# apps/wishlist/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistCreateSerializer,
    WishlistListSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer
)

logger = logging.getLogger("myapp")



class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = WishlistCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                wishlist = serializer.save()
                return Response({
                    "code": 201,
                    "message": "Wishlist created successfully",
                    "status": "success",
                    "data": {
                        "id": wishlist.id,
                        "name": wishlist.name
                    }
                }, status=201)
            return Response({
                "code": 400,
                "message": "Invalid data",
                "status": "failed",
                "errors": serializer.errors
            }, status=400)

        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Server error",
                "errors": {"server": [str(e)]}
            }, status=500)

    def get(self, request):
        try:
            wishlists = Wishlist.objects.filter(user=request.user)
            serializer = WishlistListSerializer(wishlists, many=True)

            return Response({
                "code": 200,
                "message": "Wishlists fetched",
                "status": "success",
                "data": serializer.data
            }, status=200)

        except Exception as e:
            logger.exception(str(e))
            return Response({"code": 500, "status": "failed", "message": "Server error", "errors": {"server": [str(e)]}}, status=500)



class WishlistDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.delete()
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Wishlist deleted"
            }, status=status.HTTP_204_NO_CONTENT)

        except Wishlist.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Wishlist not found",
                "errors": {
                    "wishlist": ["Wishlist not found"]
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Server error",
                "errors": {"server": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            wishlist = Wishlist.objects.get(id=pk, user=request.user)

            serializer = WishlistItemCreateSerializer(
                data=request.data,
                context={'wishlist': wishlist}
            )

            if serializer.is_valid():
                item = serializer.save()
                return Response({
                    "code": 201,
                    "message": "Item added to wishlist",
                    "status": "success",
                    "data": {"id": item.id}
                }, status=201)

            return Response(
                {"code": 400, "status": "failed", "message": "Invalid data", "errors": serializer.errors},
                status=400
            )

        except Wishlist.DoesNotExist:
            return Response({"code": 404,"status": "failed",  "message": "Wishlist not found", "errors": {"wishlist": ["Wishlist not found"]}}, status=404)
        
        except Exception as e:
           logger.exception(str(e))
           return Response({"code": 500, "status": "failed", "message": "Server error", "errors": {"server": [str(e)]}}, status=500)


    def get(self, request, pk):
        try:
            wishlist = Wishlist.objects.get(id=pk, user=request.user)
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

    def delete(self, request, pk, item_id):
        try:
            wishlist = Wishlist.objects.get(id=pk, user=request.user)
            item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
            item.delete()
            return Response({
                "code": 204,
                "message": "Item deleted from wishlist",
                "status": "success"
            }, status=204)
        except Wishlist.DoesNotExist:
            return Response({"code": 404,
                             "status": "failed",
                             "message": "Wishlist not found",
                             "errors": {"wishlist": ["Wishlist not found"]}
                             }, status=404)
        except Exception as e:
            logger.exception(str(e))
            return Response({"code": 500,
                             "status": "failed",
                             "message": "Server error",
                             "errors": {"server": [str(e)]}
                             }, status=500)

