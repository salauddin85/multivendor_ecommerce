from apps.authorization.utils.custom_permission import HasCustomPermission


class ActivityLogManagementPermission(HasCustomPermission):
    required_permission = "activity_log_management"
