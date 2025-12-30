from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category
from . import serializers
from apps.activity_log.utils.functions import log_request
from . import models
import logging
logger = logging.getLogger("myapp")
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from config.utils.pagination import CustomPageNumberPagination




class CategoriesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
       try:
           data = request.data
           serializer = serializers.CategorySerializer(data=data)
           if serializer.is_valid():
               serializer.save()
               log_request(request, "Category created", "info", "Category created successfully", response_status_code=status.HTTP_201_CREATED)  
               return Response({
                   "code": status.HTTP_201_CREATED,
                   "status": "success",
                   "message": "Category created successfully",
                   "data": serializer.data
               }, status=status.HTTP_201_CREATED)
           else:
               return Response({
                   "code": status.HTTP_400_BAD_REQUEST,
                   "status": "failed",
                   "message": "invalid request",
                   "errors": serializer.errors
               }, status=status.HTTP_400_BAD_REQUEST)
       except Exception as e:
           logger.exception(str(e))
           log_request(request, "Category creation failed", "error","Category creation failed due to server error",response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

           return Response({
               "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
               "status": "failed",
               "message": "internal server error",
               "errors": {"server_error": [str(e)]}
           }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def get(self, request):
        try:
            categories = Category.objects.all()
            paginator = CustomPageNumberPagination()
            categories = paginator.paginate_queryset(categories, request)
            serializer = serializers.CategorySerializerForView(categories, many=True)
            log_request(request, "All categories fetched", "info", "All categories fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message":"All category fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category fetch failed", "error","Category fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class CategoryDetailView(APIView):
    def get(self, request, slug):
        
        try:
            category = Category.objects.get(slug=slug)
            serializer = serializers.CategorySerializer(category)
            log_request(request, "Category fetched", "info","Category fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Category fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Category not found",
                "errors": {"detail": "Category with this ID does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category fetch failed", "error","Category fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, slug):
        try:
            category = Category.objects.get(slug=slug)
            serializer = serializers.CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_request(request, "Category updated", "info","Category updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Category updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "invalid request",
                    "errors": serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)
        
        except Category.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Category not found",
                "data": {"detail": "Category with this ID does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, slug):
        try:
            category = Category.objects.get(slug=slug)
            category.delete()
            log_request(request, "Category deleted", "info","Category deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Category deleted successfully"
                }, status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Category not found",
                "data": {
                    "detail": "Category with this ID does not exist."
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category deletion failed","error","Category deletion failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status" : "failed",
                "message" : "internal server error",
                "errors" : {"server_error" : [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
                
class CategoryTreeView(APIView):
    def get(self, request):
        try:
            # Fetch top-level categories (categories with no parent)
            top_level_categories = models.Category.objects.filter(parent__isnull=True, is_active=True).order_by('display_order')
            pagination_data = CustomPageNumberPagination()
            top_level_categories = pagination_data.paginate_queryset(top_level_categories, request)
            serializer = serializers.CategoryTreeViewSerializer(top_level_categories, many=True)
            
            log_request(request, "Category tree fetched", "info","Category tree fetched successfully", response_status_code=status.HTTP_200_OK)
            return pagination_data.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Category tree fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category tree fetch failed", "error","Category tree fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


class BrandsView(APIView):
    
    def post(self, request):
        try:
            data = request.data
            serializer = serializers.BrandSerializer(data=data)
            if serializer.is_valid():
                
                serializer.save()
                name = serializer.validated_data['name']
                log_request(request, f"Brand  {name} created", "info", f"Brand {name}  created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Brand created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "invalid request",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Brand creation failed", "error","Brand creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            brands = models.Brand.objects.filter(is_active=True).order_by('display_order')
            pagination = CustomPageNumberPagination()
            brands = pagination.paginate_queryset(brands, request)
            serializer = serializers.BrandSerializerForView(brands, many=True)
           
            log_request(request, "All brands fetched", "info", "All brands fetched successfully", response_status_code=status.HTTP_200_OK)
            return pagination.get_paginated_response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "All brands fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BrandDetailView(APIView):
    def get(self, request, slug):
        try:
            brand = models.Brand.objects.get(slug=slug)
            serializer = serializers.BrandDetailSerializer(brand)
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Brand fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except models.Brand.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Brand not found",
                "errors": {"detail": "Brand with this ID does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request,slug):
        try:
            brand = models.Brand.objects.get(slug=slug)
            serializer = serializers.BrandSerializer(brand, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Brand updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "invalid request",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except models.Brand.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Brand not found",
                "errors": {"detail": "Brand with this ID does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request,slug):
        try:
            brand = models.Brand.objects.get(slug=slug)
            brand.delete()
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Brand deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.Brand.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Brand not found",
                "errors": {"detail": "Brand with this ID does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "internal server error",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)