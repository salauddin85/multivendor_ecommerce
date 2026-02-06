# apps/reviews/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import Review
from .serializers import ReviewCreateSerializer, ReviewListSerializer

logger = logging.getLogger("reviews")

# User creates a review & list own reviews
class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                review = serializer.save()
                return Response({
                    "code": 201,
                    "status": "success",
                    "message": "Review submitted",
                    "data": {"id": review.id}
                }, status=201)
            return Response({
                "code": 400,
                "status": "failed",
                "errors": serializer.errors
            }, status=400)
        except Exception as e:
            logger.exception(str(e))
            return Response({"code": 500, "status": "failed", "errors": {"server": [str(e)]}}, status=500)

    def get(self, request):
        try:
            reviews = Review.objects.select_related('user', 'product', 'variant','vendor','store_owner','order').filter(user=request.user)
            serializer = ReviewListSerializer(reviews, many=True)
            return Response({
                "code": 200,
                "status": "success",
                "message": "Your reviews",
                "data": serializer.data
            })
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": 500, 
                "status": "failed",
                "message":"server error" ,
                "errors": {"server": [str(e)]}
                }, status=500)


# Admin or Vendor approves/rejects review
class ReviewApproveView(APIView):
    permission_classes = [IsAdminUser] 

    def patch(self, request, review_id):
       
        try:
            review = Review.objects.get(id=review_id)
            status_choice = request.data.get('status')
            if status_choice not in ['approved', 'rejected']:
                return Response({"code": 400, "status": "failed", "message": "Invalid status"}, status=400)
            review.status = status_choice
            review.save()
            return Response({
                "code": 200,
                "status": "success",
                "message": f"Review {status_choice}",
                "data": {"id": review.id}
            
            })
        
        except Review.DoesNotExist:
            return Response({
                "code": 404, 
                "status": "failed", 
                "message": "Review not found",
                "data": {"review_id": "Review not found for this id"}
                
                }, status=404)
        
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": 500, 
                "message": "Server error",
                "status": "failed",
                "errors": {"server": [str(e)]}
            }, status=500)
