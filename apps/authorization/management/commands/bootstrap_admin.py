from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from ...models import Permission, Role, AssignRole
import os
import re


class Command(BaseCommand):
    help = 'Creates initial admin and default roles & permissions'

    def handle(self, *args, **kwargs):
        self.create_admin_with_roles()

    def _clean_code(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def create_admin_with_roles(self):
        try:
            # 1Create superuser
            User = get_user_model()
            admin_email = os.getenv("ADMIN_EMAIL")
            admin_password = os.getenv("ADMIN_PASSWORD")

            if not admin_email or not admin_password:
                self.stdout.write(self.style.ERROR("ADMIN_EMAIL or ADMIN_PASSWORD is not set in environment."))
                return

            user, created = User.objects.get_or_create(
                email=admin_email,
                user_type="admin",
                defaults={"is_superuser": True, "is_staff": True}
            )
            if created:
                user.set_password(admin_password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Superuser created: {admin_email}"))
            else:
                self.stdout.write(self.style.WARNING(f"Superuser already exists: {admin_email}"))

            # 2 Create permissions
            all_permission_names = [
                "Staff onboarding", "Group permission management", "Activity log management",
                "View all users"
            ]

            permissions = []
            for perm_name in all_permission_names:
                # Using get_or_create to avoid UNIQUE constraint errors
                perm, created = Permission.objects.get_or_create(
                    name=perm_name,
                    code=self._clean_code(perm_name)
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Permission created: {perm_name}"))
                permissions.append(perm)

            #  Create 'super_admin' role and assign permissions
            role, created = Role.objects.get_or_create(name="super_admin")
            role.permissions.set(permissions)
            role.save()
            if created:
                self.stdout.write(self.style.SUCCESS("Role 'super_admin' created with all permissions."))
            else:
                self.stdout.write(self.style.SUCCESS("Role 'super_admin' updated with all permissions."))

            #  Assign role to superuser
            assign_role, created = AssignRole.objects.get_or_create(user=user)
            assign_role.roles.add(role)
            assign_role.save()
            self.stdout.write(self.style.SUCCESS(f"Assigned 'super_admin' role to {admin_email}"))

            self.stdout.write(self.style.SUCCESS("Bootstrap completed successfully!"))

        except IntegrityError as ie:
            self.stdout.write(self.style.ERROR(f"Database integrity error: {ie}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Something went wrong: {e}"))
    
    