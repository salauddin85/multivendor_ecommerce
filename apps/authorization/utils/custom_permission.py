from rest_framework.permissions import BasePermission
from ..models import Permission
from django.core.cache import cache
import pdb

class HasCustomPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if not request.user or request.user.is_anonymous:
            return False

        if self.required_permission is None:
            return False

        user = request.user
        cache_key = f"user_permissions_{user.id}"
        user_permissions = cache.get(cache_key)

        if user_permissions is None:
            print("Database hit for checking permissions..")
            user_permissions = Permission.objects.filter(
                roles__assigned_users__user=user
            ).values_list('code', flat=True).distinct()
            user_permissions = list(user_permissions)
            cache.set(cache_key, user_permissions, timeout=60*5)  # 5 minutes

        return self.required_permission in user_permissions
