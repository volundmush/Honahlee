from honahlee.core import BaseService


class AsgiService(BaseService):

    async def asgi_incoming(self, scope, receive, send):
        pass
