from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Token authorization middleware for Django Channels WebSocket connections.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Parse query string for token
        query_string = parse_qs(scope["query_string"].decode("utf8"))
        token_key = query_string.get("token")
        
        if token_key:
            token_key = token_key[0]
            scope["user"] = await get_user_from_token(token_key)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)