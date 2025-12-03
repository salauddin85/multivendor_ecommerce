from django.db import models
from django.contrib.auth import get_user_model



User = get_user_model()


class NotificationBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Notification(NotificationBaseModel):
    NOTIFY_TYPES = [
        ('new_product', 'New Product Published'),
        ('order_update', 'Order Update'),
        ('promo', 'Promotional Message'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NOTIFY_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']



class Subscriber(NotificationBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True,db_index=True)
    is_active = models.BooleanField(default=True)

