# api/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not getattr(user, "is_authenticated", False):
            await self.close()
            return

        # user group
        await self.channel_layer.group_add(f"user_{user.id}", self.channel_name)

        # role groups
        role_name = (self.scope.get("user_role") or "").lower()
        if role_name == "manager":
            await self.channel_layer.group_add("managers", self.channel_name)
        elif role_name == "admin":
            await self.channel_layer.group_add("admins", self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        user = self.scope.get("user")
        if getattr(user, "is_authenticated", False):
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)
            role_name = (self.scope.get("user_role") or "").lower()
            if role_name == "manager":
                await self.channel_layer.group_discard("managers", self.channel_name)
            elif role_name == "admin":
                await self.channel_layer.group_discard("admins", self.channel_name)

    # <- this is what Channels calls when you group_send with {"type": "notify", ...}
    async def notify(self, event):
        try:
            await self.send(text_data=json.dumps(event.get("message"), default=str))
        except Exception:
            logger.exception("Failed to send WS message")
