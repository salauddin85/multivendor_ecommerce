
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from . import serializers
from . import models
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.activity_log.utils.functions import log_request
from config.utils.pagination import CustomPageNumberPagination
from .filters import BlogFilter
logger = logging.getLogger("myapp")


class CategoryView(APIView):

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return []

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.CategorySerializer(data=data)
            if serializer.is_valid():
                category = serializer.save()
                name = serializer.validated_data["name"]
                # log the request
                log_request(request, "Category created", "info",
                            f"Category '{name}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Category created successfully",
                    "status": "success",
                    "data": {
                        "id": category.id,
                        "name": name
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log the request
                log_request(request, "Category creation failed", "error",
                            "Category creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Category creation failed", "error", "Category creation failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            categories = models.Category.objects.all().order_by('-created_at')
            serializer = serializers.CategorySerializerForView(
                categories, many=True)
            # log the request
            log_request(request, "All categories fetched", "info",
                        "All categories fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "All categories fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "All categories fetch failed", "error", "All categories fetch failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            category = models.Category.objects.get(pk=pk)
            serializer = serializers.CategorySerializer(
                category, data=request.data, partial=True)
            if serializer.is_valid():
                updated_category = serializer.save()
                log_request(request, "Category updated", "info",
                            f"Category with id {pk} updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Category updated successfully",
                    "status": "success",
                    "data": {
                        "id": updated_category.id,
                        "name": updated_category.name
                    }
                }, status=status.HTTP_200_OK)
            log_request(request, "Category update failed", "error",
                        f"Category update for id {pk} failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except models.Category.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Category not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Category with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category update failed", "error",
                        f"Category update for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            category = models.Category.objects.get(pk=pk)
            category.delete()
            log_request(request, "Category deleted", "info",
                        f"Category with id {pk} deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Category deleted successfully",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.Category.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Category not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Category with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Category deletion failed", "error",
                        f"Category deletion for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TagView(APIView):

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return []

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.TagSerializer(data=data)
            if serializer.is_valid():
                tag = serializer.save()
                name = serializer.validated_data["name"]
                # log the request
                log_request(request, "Tag created", "info",
                            f"Tag '{name}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Tag created successfully",
                    "status": "success",
                    "data": {
                        "id": tag.id,
                        "name": name
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log the request
                log_request(request, "Tag creation failed", "error", "Tag creation failed due to invalid data",
                            response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Tag creation failed", "error", "Tag creation failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            tags = models.Tag.objects.all().order_by('-created_at')
            serializer = serializers.TagSerializerForView(tags, many=True)
            # log the request
            log_request(request, "All tags fetched", "info",
                        "All tags fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "All tags fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "All tags fetch failed", "error", "All tags fetch failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TagDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            tag = models.Tag.objects.get(pk=pk)
            tag.delete()
            log_request(request, "Tag deleted", "info",
                        f"Tag with id {pk} deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Tag deleted successfully",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.Tag.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Tag not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Tag with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Tag deletion failed", "error",
                        f"Tag deletion for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            tag = models.Tag.objects.get(pk=pk)
            serializer = serializers.TagSerializer(
                tag, data=request.data, partial=True)
            if serializer.is_valid():
                updated_tag = serializer.save()
                log_request(request, "Tag updated", "info",
                            f"Tag with id {pk} updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Tag updated successfully",
                    "status": "success",
                    "data": {

                        "id": updated_tag.id,
                        "name": updated_tag.name
                    }
                }, status=status.HTTP_200_OK)
            log_request(request, "Tag update failed", "error",
                        f"Tag update for id {pk} failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except models.Tag.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Tag not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Tag with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Tag update failed", "error",
                        f"Tag update for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlogView(APIView):

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return []

    def post(self, request):
        try:
            user = request.user
            data = request.data
            serializer = serializers.BlogSerializer(
                data=data, context={"user": user})
            if serializer.is_valid():
                blog = serializer.save()
                title = serializer.validated_data["title"]
                # log the request
                log_request(request, "Blog created", "info",
                            f"Blog '{title}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Blog created successfully",
                    "status": "success",
                    "data": {
                              "id": blog.id,
                              "blog_title": title
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log the request
                log_request(request, "Blog creation failed", "error",
                            "Blog creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Blog creation failed", "error", "Blog creation failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "error occurred",
                "status": "failed",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            queryset = models.Blog.objects.all().order_by("-created_at")
            paginator = CustomPageNumberPagination()
            filterset = BlogFilter(request.GET, queryset=queryset)
            if not filterset.form.is_valid():
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid filter parameters",
                    "status": "failed",
                    "errors": filterset.form.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            queryset = filterset.qs
            page = paginator.paginate_queryset(queryset, request)
            serializer = serializers.BlogSerializerForView(page, many=True)
            response_data = {
                "code": status.HTTP_200_OK,
                "message": "Blogs fetched successfully",
                "status": "success",
                "data": serializer.data
            }
            # log the request
            log_request(request, "Blogs retrieved", "info",
                        "Fetched blog list successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response(response_data)

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Blogs retrieval failed", "error", "Fetching blogs failed due to server error",
                        response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "error occurred",
                "status": "failed",
                "errors": {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlogDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return []

    def get(self, request, pk):
        try:
            blog = models.Blog.objects.get(pk=pk)
            serializer = serializers.BlogSpecificDetailSerializer(blog)
            log_request(request, "Blog detail fetched", "info",
                        f"Blog detail for id {pk} fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Blog detail fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except models.Blog.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Blog not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Blog with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Blog detail fetch failed", "error",
                        f"Blog detail fetch for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            blog = models.Blog.objects.get(pk=pk)
            serializer = serializers.BlogSerializer(
                blog, data=request.data, partial=True)

            if serializer.is_valid():
                updated_blog = serializer.save()
                log_request(request, "Blog updated", "info",
                            f"Blog with id {pk} updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Blog updated successfully",
                    "status": "success",
                    "data": {
                        "id": updated_blog.id,
                        "blog_title": updated_blog.title
                    }
                }, status=status.HTTP_200_OK)
            log_request(request, "Blog update failed", "error",
                        f"Blog update for id {pk} failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except models.Blog.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Blog not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Blog with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Blog update failed", "error",
                        f"Blog update for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            blog = models.Blog.objects.get(pk=pk)
            blog.delete()
            log_request(request, "Blog deleted", "info",
                        f"Blog with id {pk} deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Blog deleted successfully",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.Blog.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Blog not found",
                "status": "failed",
                "errors": {
                    'not_found': [f"Blog with id {pk} does not exist."]
                },
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Blog deletion failed", "error",
                        f"Blog deletion for id {pk} failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
