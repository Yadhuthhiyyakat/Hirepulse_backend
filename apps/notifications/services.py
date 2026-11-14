import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

logger = logging.getLogger(__name__)

def create_notification(user, title, message, notification_type='SYSTEM', data=None):
    """
    Creates a notification in the database and broadcasts it over WebSockets.
    """
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {}
    )

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"user_{user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'notification': {
                        'id': str(notification.id),
                        'title': notification.title,
                        'message': notification.message,
                        'notification_type': notification.notification_type,
                        'data': notification.data,
                        'is_read': notification.is_read,
                        'created_at': notification.created_at.isoformat()
                    }
                }
            )
    except Exception as e:
        logger.warning(f"Could not broadcast notification over channel layer: {e}")

    return notification

