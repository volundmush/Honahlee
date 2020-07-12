from honahlee.core import BaseService
from honahlee.utils.misc import import_from_module
from channels.routing import ProtocolTypeRouter
from hypercorn.config import Config
from channels.routing import URLRouter
from django.conf.urls import url

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.consumer import AsyncConsumer
from channels.auth import AuthMiddlewareStack


class LifespanAsyncConsumer(AsyncConsumer):
    service = None

    async def lifespan_startup(self, event):
        await self.send({
            'type': 'lifespan.startup.complete'
        })

    async def lifespan_startup_complete(self, event):
        pass

    async def lifespan_startup_failed(self, event):
        pass

    async def lifespan_shutdown(self, event):
        await self.send({
            'type': 'lifespan.shutdown.complete'
        })

    async def lifespan_shutdown_complete(self, event):
        pass

    async def lifespan_shutdown_failed(self, event):
        pass


class GameConsumer(AsyncWebsocketConsumer):
    service = None

    async def connect(self):
        await self.accept()
        print(f"RECEIVED A GAME CONNECTION: {self.scope}")

    async def disconnect(self, code):
        print(f"CLOSED {self} with {code}")


class LinkConsumer(AsyncWebsocketConsumer):
    service = None

    async def connect(self):
        await self.accept()
        print(f"RECEIVED A LINK CONNECTION: {self.scope}")

    async def disconnect(self, code):
        print(f"CLOSED {self} with {code}")


class WebService(BaseService):

    def __init__(self, app):
        super().__init__(app)
        self.task = None
        self.config = None
        self.asgi_app = None
        self.consumer_classes = dict()

    async def setup(self):

        self.config = Config()
        self.config.bind = [f"{self.app.settings.INTERFACE}:{self.app.settings.WEB_PORT}"]

        # Import all of the Consumers and set them to have a reference to this Service.
        for k, v in self.app.settings.CONSUMER_CLASSES.items():
            found = import_from_module(v)
            found.service = self
            self.consumer_classes[k] = found

        self.asgi_app = ProtocolTypeRouter(self.get_protocol_router_config())

    def get_protocol_router_config(self):
        return {
            "websocket": self.get_protocol_websocket_config(),
            "lifespan": self.consumer_classes["lifespan"],
            "telnet": AuthMiddlewareStack(self.consumer_classes["telnet"])
        }

    def get_protocol_websocket_config(self):

        return AuthMiddlewareStack(URLRouter([
            url(r"^game/$", self.consumer_classes["game"]),
            url(r"^link/$", self.consumer_classes["link"])
        ]))

    def get_protocol_router_http_config(self):
        pass

    async def start(self):
        import asyncio
        loop = asyncio.get_event_loop()
        from hypercorn.asyncio import serve
        self.task = loop.create_task(serve(self.asgi_app, self.config))

