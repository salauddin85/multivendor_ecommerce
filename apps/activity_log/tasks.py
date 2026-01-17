from django.contrib.auth import get_user_model
from apps.activity_log.models import ActivityLog

import logging
from django.conf import settings
from django_redis import get_redis_connection
import json
from config.celery import app
from django.utils import timezone
from datetime import timedelta


logger = logging.getLogger("myapp")


def enqueue_activity_log(data):
    """Queue activity log in Redis (only for production)"""
    try:

        conn = get_redis_connection("default")
        conn.rpush("activity_log_queue", json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis queue failed, saving directly: {str(e)}")
        save_activity_log_to_db(data)


def save_activity_log_to_db(data):
    """Save activity log directly to database"""

    try:
        ActivityLog.objects.create(
            user_id=data.get('user'),
            ip_address=data.get('ip_address'),
            location=data.get('location'),
            user_agent=data.get('user_agent'),
            request_method=data.get('request_method'),
            referrer_url=data.get('referrer_url'),
            device=data.get('device'),
            path=data.get('path'),
            verb=data.get('verb'),
            severity_level=data.get('severity_level'),
            description=data.get('description'),
            response_status_code=data.get('response_status_code'),
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save activity log: {str(e)}")
        return False


@app.task
def log_activity_task(data, verb, severity_level, description, response_status_code=None):
    """Celery task to log user activity asynchronously."""
    try:
        user_id = data.get("user_id")
        method = data.get("method")
        path = data.get("path")
        ip = data.get("ip")
        location = data.get("location")
        user_agent = data.get("user_agent")
        device = data.get("device")
        referrer_url = data.get("referrer_url")

        dict_data = {
            'user': user_id,
            'ip_address': ip,
            'location': location,
            'user_agent': user_agent,
            'request_method': method,
            'referrer_url': referrer_url,
            'device': device,
            'path': path,
            'verb': verb,
            'severity_level': severity_level,
            'description': description,
            'response_status_code': response_status_code if response_status_code is not None else "",
        }

        enqueue_activity_log(dict_data)

        return {"status": "success", "details": "Logged successfully"}

    except Exception as e:
        logger.exception(str(e))
        return {"status": "error", "error": str(e)}


@app.task
def flush_activity_logs():
    conn = get_redis_connection("default")
    logs = []

    while True:
        raw = conn.lpop("activity_log_queue")
        if raw is None:
            break
        logs.append(json.loads(raw))

    logs_to_create = []
    User = get_user_model()

    for log in logs:
        user = None
        if log.get("user"):
            try:
                user = User.objects.get(id=log["user"])
            except User.DoesNotExist:
                pass

        logs_to_create.append(ActivityLog(
            user=user,
            ip_address=log["ip_address"],
            location=log["location"],
            user_agent=log["user_agent"],
            request_method=log["request_method"],
            referrer_url=log["referrer_url"],
            device=log["device"],
            path=log["path"],
            verb=log["verb"],
            severity_level=log["severity_level"],
            description=log["description"],
            response_status_code=log["response_status_code"] if "response_status_code" in log else None,
        ))

    if logs_to_create:
        for i in range(0, len(logs_to_create), 100):
            ActivityLog.objects.bulk_create(logs_to_create[i:i+100])
        return f"{len(logs_to_create)} logs flushed"
    return "No logs to flush"




@app.task
def delete_activity_logs_older_than_one_month():
    cutoff_date = timezone.now() - timedelta(days=30)

    # Bulk delete in a single SQL query
    deleted_count, _ = ActivityLog.objects.filter(
        timestamp__lt=cutoff_date).delete()

    return f"Deleted {deleted_count} old activity logs"
