from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model


class ActivityLog(models.Model):
    user = models.ForeignKey(get_user_model(
    ), on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    ip_address = models.GenericIPAddressField(default="", blank=False)
    location = models.JSONField(default=dict, blank=True)
    user_agent = models.TextField(default="Unknown", blank=True)
    request_method = models.CharField(max_length=10, default="", blank=True)
    severity_level = models.CharField(
        max_length=50,
        choices=[("info", "Info"), ("warning", "Warning"),
                 ("error", "Error"), ("critical", "Critical")],
        default="info"
    )
    referrer_url = models.TextField(default="", blank=True)
    device = models.CharField(
        max_length=255, default="Unknown Device", blank=True)
    path = models.CharField(max_length=255, default="/", blank=True)
    verb = models.CharField(max_length=250, default="", blank=True)
    description = models.TextField(default="", blank=True)
    response_status_code = models.IntegerField(default="", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Activity log for {self.user} at {self.timestamp} - {self.verb}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Activity Logs"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['severity_level']),
        ]