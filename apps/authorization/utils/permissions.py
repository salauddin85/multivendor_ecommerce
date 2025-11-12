


from apps.authorization.utils.custom_permission import HasCustomPermission

class RegisterUserPermission(HasCustomPermission):
    required_permission = "staff_onboarding"


class GroupPermissionManagement(HasCustomPermission):
    required_permission = "group_permission_management"


class ViewAllUserPermission(HasCustomPermission):
    required_permission = "view_all_users"