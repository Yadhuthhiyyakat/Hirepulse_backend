from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel

class NotificationType(models.TextChoices):
    STATUS_UPDATE = 'STATUS_UPDATE', 'Status Update'
    INTERVIEW = 'INTERVIEW', 'Interview Invitation'
    NEW_APPLICATION = 'NEW_APPLICATION', 'New Applicant'
    JOB_ALERT = 'JOB_ALERT', 'Job Alert'
    SYSTEM = 'SYSTEM', 'System Notification'

class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True
    )
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} (Read: {self.is_read})"

