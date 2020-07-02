from honahlee.core import BaseService


class AsgiService(BaseService):
    """
    This service
    """

    async def asgi_incoming(self, scope, receive, send):
        pass
