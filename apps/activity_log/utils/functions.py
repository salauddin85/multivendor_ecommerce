from django.conf import settings
from apps.activity_log.tasks import log_activity_task
import requests
import logging
logger = logging.getLogger("myapp")


def get_client_ip(request):
    """Extract real IP address from headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")


def request_data_activity_log(request):
    client_ip = get_client_ip(request)
    # client_ip = "8.8.8.8"
    if request.user is not None:
        user_id = request.user.id
    else:
        user_id = None
    data = {
        "user_id": user_id,
        "method": request.method,
        "path": request.path,
        "ip": client_ip,
        "location": "BD",
        "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
        "device": request.META.get("COMPUTERNAME", "Unknown Device"),
        "referrer_url": request.META.get("HTTP_REFERER", "None"),

    }
    return data


def log_request(request, message, severity_level, description, response_status_code=None):
    task_data = request_data_activity_log(request)

    # production asynchronously queue
    try:
        log_activity_task.delay_on_commit(
            task_data,
            verb=message,
            severity_level=severity_level,
            description=description,
            response_status_code=response_status_code
        )
    except Exception as e:
        logger.error(f"Failed to queue activity log: {str(e)}")
