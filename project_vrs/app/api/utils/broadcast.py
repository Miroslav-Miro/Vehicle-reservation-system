# api/utils/broadcast.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from api.models import Notification  # absolute import (no relative confusion)

def broadcast_notification(message: dict, *, user_id: int | None = None, roles: list[str] | None = None):
    """
    Persist a DB notification for the given user_id and push WS messages.
    Runs AFTER the surrounding DB transaction commits, so readers immediately see the row.

    :param message: The notification message to send.
    :type message: dict
    :param user_id: The ID of the user to notify (optional).
    :type user_id: int | None
    :param roles: List of role names to notify (optional).
    :type roles: list[str] | None
    :return: None
    :rtype: None
    """

    def _do():
        ch = get_channel_layer()

        if user_id:
            # Works for FK recipient or int recipient_id
            Notification.objects.create(
                recipient_id=user_id,
                message=message.get("message") or message.get("action") or "",
                type=message.get("action") or "info",
                is_read=False,
            )
            async_to_sync(ch.group_send)(
                f"user_{user_id}", {"type": "notify", "message": message}
            )

        if roles:
            for role in roles:
                async_to_sync(ch.group_send)(
                    role, {"type": "notify", "message": message}
                )

    # Defer both DB write and WS push until the outer transaction commits
    transaction.on_commit(_do)
