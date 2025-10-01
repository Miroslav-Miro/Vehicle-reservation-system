# api/middleware/token_auth.py
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack   # safe at import time
from channels.db import database_sync_to_async  # safe at import time

@database_sync_to_async
def _resolve_user_and_role(token):
    # Import Django/DRF *inside* the function (after apps are ready)
    from django.contrib.auth.models import AnonymousUser
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from api.models import User  # OK here; apps are ready once this runs

    try:
        auth = JWTAuthentication()
        validated = auth.get_validated_token(token)
        user = auth.get_user(validated)

        # Your FK is named 'role_id'; fetch role_name without extra queries
        u = User.objects.select_related("role_id").only("id", "role_id__role_name").get(pk=user.id)
        role_obj = getattr(u, "role", None) or getattr(u, "role_id", None)
        role_name = (getattr(role_obj, "role_name", "") or "").lower()

        return user, role_name
    except Exception:
        return AnonymousUser(), ""

class TokenAuthMiddleware:
    """
    Custom middleware that takes a token from the query string
    and authenticates via JWT, populating scope["user"] and scope["user_role"].
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse token from query string
        q = parse_qs(scope.get("query_string", b"").decode())
        token = (q.get("token") or [None])[0]

        if token:
            user, role_name = await _resolve_user_and_role(token)
        else:
            # Lazy import here too to avoid top-level import
            from django.contrib.auth.models import AnonymousUser
            user, role_name = AnonymousUser(), ""

        scope["user"] = user
        scope["user_role"] = role_name  # put plain string into scope (no ORM in consumer)
        return await self.inner(scope, receive, send)

def TokenAuthMiddlewareStack(inner):
    """
    Custom middleware stack that includes TokenAuthMiddleware.

    :param inner: The inner application to wrap.
    :type inner: ASGI application
    :return: The wrapped ASGI application with token authentication.
    :rtype: ASGI application
    """
    # Don’t import AuthMiddleware in __call__, just wrap here
    return AuthMiddlewareStack(TokenAuthMiddleware(inner))
