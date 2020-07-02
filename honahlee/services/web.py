import asyncio
from honahlee.core import BaseService
from hypercorn.asyncio import serve
from hypercorn.config import Config


class WebService(BaseService):

    def __init__(self, app):
        super().__init__(app)
        self.task = None
        self.config = Config()

    async def setup(self):
        self.config.bind = [f"{self.app.settings.INTERFACE}:{self.app.settings.WEB_PORT}"]

    async def start(self):
        asyncio.create_task(serve(self.accept, self.config))

    async def accept(self, scope, reader, writer):
        if scope['type'] == 'lifespan':
            message = await reader()
            if message['type'] == 'lifespan.startup':
                await writer({'type': 'lifespan.startup.complete'})
                print("THIS RETURNS!")
                return
