
import logging
from unicodedata import name
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from . import serializers
from . import models
from django.db import transaction

from apps.authorization.utils.permissions import GroupPermissionManagement,ViewAllUserPermission,RegisterUserPermission
from apps.activity_log.utils.functions import log_request
from .utils.function import clear_user_permissions_cache
from django.db.models import Count
from django.contrib.auth import get_user_model
from .tasks import send_otp_email
from config.utils.pagination import CustomPageNumberPagination
from apps.authentication.models import StoreOwner,Staff,Vendor,Customer

logger = logging.getLogger("myapp")




class PermissionView(APIView):
    permission_classes = [IsAuthenticated, GroupPermissionManagement]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.PermissionSerializer(data=data)

            if serializer.is_valid():
                permission = serializer.save()
                name = serializer.validated_data["name"]
                
                # log the request
                log_request(request, "Permission created", "info", f"Permission '{name}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Permission created successfully",
                    "status": "success",
                    "data": {
                        "id": permission.id,
                        "permission_name": name
                    }
                }, status=status.HTTP_201_CREATED)
            # log the request
            log_request(request, "Permission creation failed", "error", "Permission creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response(
                {
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Permission creation failed", "error", "Permission creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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
            all_permission = models.Permission.objects.all()
            serializer = serializers.PermissionSerializerForView(
                all_permission, many=True)
            
            # log the request
            log_request(request, "All permissions fetched", "info", "All permissions fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response(
                {
                    "code": status.HTTP_200_OK,
                    "message": "All permissions fetched successfully",
                    "status": "success",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "All permissions fetch failed", "error", "All permissions fetch failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, GroupPermissionManagement]

    def patch(self, request, id):
        try:
            permission = models.Permission.objects.get(id=id)
            serializer = serializers.PermissionSerializer(
                permission, data=request.data, partial=True)
            if serializer.is_valid():
                updated_permission = serializer.update(permission, serializer.validated_data)
                # log the request
                log_request(request, "Permission updated", "info", f"Permission '{updated_permission.name}' updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Permission updated successfully",
                    "status": "success",
                    "data": {
                        "id": updated_permission.id,
                        "name": updated_permission.name,
                        "code": updated_permission.code
                    }
                }, status=status.HTTP_200_OK)
            else:
                # log the request
                log_request(request, "Permission update failed", "error", "Permission update failed due to  invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except models.Permission.DoesNotExist:
            # log the request
            log_request(request, "Permission update failed", "error", "Permission update failed due to not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Permission not found",
                "status": "failed",
                "errors": {
                    "permission": ["Permission not found for the given ID."]
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Permission update failed", "error", "Permission update failed due to  server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            permission = models.Permission.objects.get(id=id)
            permission.delete()
            # log the request
            log_request(request, "Permission deleted", "info", "Permission  deleted successfully", response_status_code=status.HTTP_204_NO_CONTENT)
            return Response({
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Permission deleted successfully",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        except models.Permission.DoesNotExist:
            # log the request
            log_request(request, "Permission deletion failed", "error", "Permission deletion failed due to not found", response_status_code=status.HTTP_404_NOT_FOUND)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Permission not found",
                "status": "failed",
                "errors": {
                    "permission": ["Permission not found for the given ID."]
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Permission deletion failed", "error", "Permission deletion failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class RolePermissionView(APIView):
    def get_permissions(self):

        if self.request.method == "POST":
            return [GroupPermissionManagement()]
        elif self.request.method == "GET":
            return [GroupPermissionManagement()]
        elif self.request.method == "DELETE":
            return [GroupPermissionManagement()]
        else:
            return [IsAuthenticated()]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.RoleModelSerializer(
                data=data)
            if serializer.is_valid():
                role = serializer.save()
                permissions = role.permissions.all()
                permission_ids = [perm.id for perm in permissions]
                # log request
                log_request(request, "Role created", "info", f"Role '{role.name}' created successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Operation successfully",
                    "status": "success",
                    "data": {
                        "id": role.id,
                        "name": role.name,
                        "permissions": permission_ids
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # log request
                log_request(request, "Role creation failed", "error", "Role creation failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Role creation failed", "error", "Role creation failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "invalid request",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:

            data = models.Role.objects.all()
            serializer = serializers.RoleSerializerForView(data, many=True)
            log_request(request, "Role retrieval successful", "info", "Roles retrieved successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "operation successful",
                "status": "success",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Role retrieval failed", "error", "Role retrieval failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        data = request.data
        role = data.get('role')
        permission = data.get('permission')
        try:
            role_obj = models.Role.objects.get(id=role)
            if role_obj:
                permission_exists = role_obj.permissions.filter(
                    id=permission).exists()
                if permission_exists:
                    role_obj.permissions.remove(permission)
                else:
                    log_request(request, "Role permission removal failed", "error", "Role permission removal failed due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                    return Response({
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Operation failed",
                        "status": "failed",
                        "data": {
                            "permission": ["Permission does not exist in the role"]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            clear_user_permissions_cache()
            log_request(request, "Role permission removed", "info", "Role permission removed successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Operation successful",
                "status": "success",
                "detail": "Permission deleted successfully"
            }, status=status.HTTP_200_OK)

        except models.Role.DoesNotExist:
            log_request(request, "Role permission removal failed", "error", "Role permission removal failed due to group not found", response_status_code=status.HTTP_400_BAD_REQUEST)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Operation failed",
                "status": "failed",
                "data": {
                    "group": ["Group does not exist"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Role permission removal failed", "error", "Role permission removal failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RolePermissionViewV2(APIView):
    permission_classes = [IsAuthenticated, GroupPermissionManagement]

    def get(self, request):
        try:
            data = models.Role.objects.annotate(
                permission_count=Count('permissions', distinct=True),
                user_count=Count("assigned_users__user", distinct=True)
            )
            serializer = serializers.RoleSerializerForViewAllRolesV2(data, many=True)
            log_request(request, "Fetched all roles with permission count and user count", "info", "Fetched all roles with permission count and user count successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Fetched all available roles with permission count and user count.",
                "status": "success",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch roles with permission count and user count", "error", "Failed to fetch roles with permission count and user count due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SpecificRolePermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ["DELETE", "PATCH"]:
            return [IsAuthenticated(), GroupPermissionManagement()]
        return [IsAuthenticated()]

    def patch(self, request, role_id):
        """Update a role with required permissions at least one permission"""
        try:
            role = get_object_or_404(models.Role, pk=role_id)
            serializer = serializers.RoleModelSerializer(
                role, data=request.data)
            if serializer.is_valid():
                serializer.save()
                # after updating the role delete the permissions cache
                clear_user_permissions_cache()

                log_request(request, "Updated a role", "info", "Updated a role with required permissions successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Operation successful",
                    "status": "success",
                    'data': serializer.data
                })
            else:
                log_request(request, "Failed to update a role", "error", "Failed to update a role due to invalid data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to update a role", "error", "Failed to update a role due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, role_id):
        """Delete a role"""

        try:
            role = get_object_or_404(models.Role, pk=role_id)
            role.delete()
            # clear permissions cache for all users after a role deletion
            clear_user_permissions_cache()
            log_request(request, "Deleted a role", "info", "Deleted a role successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Operation successful",
                "status": "success",
                'detail': f"Role deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to delete a role", "error", "Failed to delete a role due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AssignRolePermissionView(APIView):
    permission_classes = [IsAuthenticated,
                          GroupPermissionManagement]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.AssignRolePermissionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                roles = serializer.validated_data.get("roles")
                user = serializer.validated_data.get("user")

                roles_data = []
                for role in roles:
                    roles_data.append(
                        {"role_id": role.id, "role_name": role.name})
                clear_user_permissions_cache()
                # log the request
                log_request(request, "Assigned role to user", "info", "Role assigned to user successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Assign role to user successful",
                    "status": "success",
                    "user_id": user.id,
                    "roles": roles_data
                }, status=status.HTTP_201_CREATED)

            else:
                
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Failed to assign role to user", "error", "Failed to assign role to user due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            serializer = serializers.DeleteUserFromRoleSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user_id']
                role = serializer.validated_data['role_id']
                assign_role = models.AssignRole.objects.get(user=user)
                assign_role.roles.remove(role)
                assign_role.save()
                clear_user_permissions_cache()
                # log the request
                log_request(request, "Removed user from role", "info", "User removed from role successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Operation successful",
                    "status": "success",
                    "detail": "User removed from role successfully."
                }, status=status.HTTP_200_OK)
            else:
                
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to remove user from role", "error", "Failed to remove user from role due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    "server_error": [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:

            data = models.AssignRole.objects.all()
            users_data = []
            for assign_role in data:
                user_info = {
                    "user_id": assign_role.user.id if assign_role.user else None,
                    "email": assign_role.user.email if assign_role.user else "No User",
                    "user_type": assign_role.user.user_type if assign_role.user else "No User",
                    "roles": []
                }
                for role in assign_role.roles.all():
                    role_info = {
                        "role_id": role.id,
                        "role_name": role.name,
                        "permissions": [
                            {"permission_id": perm.id, "permission_name": perm.name}
                            for perm in role.permissions.all()
                        ]
                    }
                    user_info["roles"].append(role_info)
                users_data.append(user_info)
            # log the request
            log_request(request, "Fetched all users with their roles", "info", "All users with their roles fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "All users with their roles fetched successfully",
                "status": "success",
                "data": users_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Failed to retrieve user roles", "error", "Failed to retrieve user roles due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                "errors": {
                    "server_error": [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        try:
            data = request.data
            
            serializer = serializers.AssignRolesUpdateSerializer(
            data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                user_id = serializer.validated_data["user"].id
                roles = serializer.validated_data["roles"]
                roles_data = [{"role_id": ro.id,
                                "role_name": ro.name} for ro in roles]
                clear_user_permissions_cache()
                # log the request
                log_request(request, "Updated user roles", "info", f"User roles updated successfully", response_status_code=status.HTTP_200_OK)
                return Response({
                    "code": status.HTTP_200_OK,
                    "message": "Operation successful",
                    "status": "success",
                    "data": {
                         "user_id": user_id,
                         "updated_groups": roles_data
                    }
                }, status=status.HTTP_200_OK)
            else:
                
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Failed to assign role to multiple users", "error", "Failed to assign role to multiple users due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors":
                {
                    'server_error': [str(e)]
                }
            }, status=status.HTTP_400_BAD_REQUEST)




class AssignRolePermissionView2(APIView):
    permission_classes = [IsAuthenticated,
                          GroupPermissionManagement]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.AssignRolePermissionSerializer2(data=data)
            if serializer.is_valid():
               
                serializer.save()
                role = serializer.validated_data.get("role")
                users = serializer.validated_data.get("users")

                users_data = []
                for user in users:
                    users_data.append(
                        {"user_id": user.id, "email": user.email})
                clear_user_permissions_cache()
                # log the request
                log_request(request, "Assigned role to multiple users", "info", f"Role '{role.name}' assigned to multiple users successfully", response_status_code=status.HTTP_201_CREATED)
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Assign role to multiple users successful",
                    "status": "success",
                    "data":{
                        "user": users_data,
                        "role": {
                            "role_id": role.id,
                            "role_name": role.name
                        }
                    }
                }, status=status.HTTP_201_CREATED)

            else:
               
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Failed to assign role to multiple users", "error", "Failed to assign role to multiple users due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {'server_error': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ViewAllUserView(APIView):
    permission_classes = [IsAuthenticated, ViewAllUserPermission]

    def get(self, request):
        try:
            data = get_user_model().objects.all().order_by("id")
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(
                data, request, view=self)
            serializer = serializers.UserSerializer(paginated_queryset, many=True)
            # log the request
            log_request(request, "Viewing all users", "info", "Viewed all available users successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                'code': 200,
                'status': 'success',
                'message': "Viewing all available users",
                'data': serializer.data
            }, status=200)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Viewing all users failed", "error", "Viewing all users failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class OnboardingStaffView(APIView):
    permission_classes = [IsAuthenticated, RegisterUserPermission]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.StaffOnboardingSerializer(
                data=data)
            if serializer.is_valid():
                with transaction.atomic():
                    instance = serializer.save()
                    email = serializer.validated_data["email"]
                    try:
                        otp = models.OTP.objects.get(email=email)
                        otp_value = otp.otp
                        send_otp_email.delay_on_commit(email, otp_value)

                    except models.OTP.DoesNotExist:
                        return Response({
                            "code": status.HTTP_404_NOT_FOUND,
                            "message": "Invalid request",
                            "status": "failed",
                            "errors": {
                                'otp': ["OTP for the provided email does not exist."]
                            }}, status=status.HTTP_404_NOT_FOUND)
                    
                    response = Response({
                        "code": status.HTTP_201_CREATED,
                        "message": "Operation successful",
                        "status": "success",
                        "message": "OTP sent successfully. OTP is valid for 10 minutes.",
                        "to": {
                            "email": email,
                        }
                    }, status=status.HTTP_201_CREATED)
                    # log the request
                    log_request(request, "Onboarding OTP sent", "info", f"OTP sent successfully to '{email}' for onboarding", response_status_code=status.HTTP_201_CREATED)
                    return response
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Onboarding OTP sending failed", "error", "OTP sending for onboarding failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingStaffVerifyView(APIView):
    permission_classes = [IsAuthenticated, RegisterUserPermission]

    def post(self, request):
        try:
            data = request.data
            serializer = serializers.StaffOnboardingVerifyOtpSerializer(
                data=data)
            if serializer.is_valid():
                email = serializer.validated_data["email"]
                otp = serializer.validated_data["otp"]
                otp_object = models.OTP.objects.get(email=email, otp=otp)
                otp_object.delete()
                try:
                    models.VerifySuccessfulEmail.objects.create(email=email)
                except Exception as e:
                    logger.exception(str(e))
                    # log the request
                    log_request(request, "Email verification failed", "error", "Email verification failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    return Response({
                        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Invalid request",
                        "status": "failed",
                        "errors": {
                            'email': [str(e)]
                        }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                # log the request
                response = Response({
                                    "code": status.HTTP_200_OK,
                                    "message": "Email verified successfully.",
                                    "status": "success",
                                    "email": email,
                                    }, status=status.HTTP_200_OK)
                log_request(request, "Email verified", "info", f"Email '{email}' verified successfully", response_status_code=status.HTTP_200_OK)
                return response
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Email verification failed", "error", "Email verification failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingStaffRegisterView(APIView):
    permission_classes = [IsAuthenticated, RegisterUserPermission]

    def post(self, request):
        try:
            user=request.user
            data = request.data
            serializer = serializers.StaffOnboardingRegistrationSerializer(
                data=data, context={"requester": user})
            if serializer.is_valid():
                user = serializer.save()
                email = serializer.validated_data["email"]
                # log the request
                log_request(request, "Staff onboarding", "info", f"Staff '{email}' onboarded successfully", response_status_code=status.HTTP_201_CREATED)

                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Operation successful",
                    "status": "success",
                    "email": email
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Staff onboarding failed", "error", "Staff onboarding failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ViewSingleUserRolesPermissionsView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        try:
            user = request.user  

            # Fetch assigned roles for this user
            try:
                assign_role = models.AssignRole.objects.get(user=user)
                roles = assign_role.roles.all()
            except models.AssignRole.DoesNotExist:
                roles = []

            # Collect role names
            role_names = [role.name for role in roles]

            # Collect permissions from all assigned roles
            permission_set = set()
            for role in roles:
                permission_set.update(role.permissions.values_list('code', flat=True))

            # Prepare the response
            data = {
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_type": getattr(user, 'user_type', None),
                    "is_active": user.is_active,
                    "is_staff": user.is_staff,
                },
                "roles": role_names,
                "permissions": list(permission_set),
            }
            log_request(request, "Fetched user roles and permissions", "info", "User roles and permissions fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "User roles and permissions fetched successfully",
                "status": "success",
                "data": data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch user roles and permissions", "error", "Failed to fetch user roles and permissions due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
   


class RoleDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            role = models.Role.objects.prefetch_related(
                "permissions").get(id=id)
            
            # Serialize role details
            role_serializer = serializers.RoleSerializerForView(role)

            # Get users assigned to this role
            assigned_roles = models.AssignRole.objects.filter(roles=role).select_related('user')
            users = [ar.user for ar in assigned_roles if ar.user]
            user_serializer = serializers.UserSerializer(users, many=True)

            log_request(request, "Role details fetched", "info",
                        f"Details for role '{role.name}' fetched successfully", response_status_code=status.HTTP_200_OK)
            return Response({
                "code": 200,
                "status": "success",
                "data": {
                    "role": role_serializer.data,
                    "users": user_serializer.data
                }
            }, status=status.HTTP_200_OK)

        except models.Role.DoesNotExist:
            return Response({"code": status.HTTP_404_NOT_FOUND, "message": "Role not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Role details fetch failed", "error",
                        f"Role details fetch failed due to server error: {str(e)}", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Invalid request",
                "status": "failed",
                "errors": {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



            

class AllStaffListView (APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            staff_members = Staff.objects.select_related('user', 'store_owner').all()
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(
                staff_members, request, view=self)
            serializer = serializers.StaffSerializer(staff_members, many=True)
            log_request(request, "Fetched all staff members", "info", "All staff members fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "message": "All staff members fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch staff members", "error", "Failed to fetch staff members due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
class AllVendorListView (APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            vendors = Vendor.objects.select_related('user').all()
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(
                vendors, request, view=self)
            serializer = serializers.VendorSerializer(paginated_queryset, many=True)
            log_request(request, "Fetched all vendors", "info", "All vendors fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "message": "All vendors fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch vendors", "error", "Failed to fetch vendors due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class AllCustomerListView (APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            customers = Customer.objects.select_related('user').all()
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(
                customers, request, view=self)
            serializer = serializers.CustomerSerializer(paginated_queryset, many=True)
            log_request(request, "Fetched all customers", "info", "All customers fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "message": "All customers fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch customers", "error", "Failed to fetch customers due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AllStoreOwnerListView (APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]

    def get(self, request):
        try:
            store_owners = StoreOwner.objects.select_related('user').all()
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(
                store_owners, request, view=self)
            serializer = serializers.StoreOwnerSerializer(store_owners, many=True)
            log_request(request, "Fetched all store owners", "info", "All store owners fetched successfully", response_status_code=status.HTTP_200_OK)
            return paginator.get_paginated_response({
                "code": status.HTTP_200_OK,
                "message": "All store owners fetched successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Failed to fetch store owners", "error", "Failed to fetch store owners due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)