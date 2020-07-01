import asyncio
import uuid
import datetime


class BaseProtocol:

    def __init__(self, server, reader, writer):
        self.server = server
        self.service = server.service
        self.app = self.service.app
        self.reader = reader
        self.writer = writer
        self.bytes_sent = 0
        self.bytes_received = 0
        self.creation_datetime = datetime.datetime.utcnow()
        self.last_received = datetime.datetime.utcnow()
        self.last_sent = datetime.datetime.utcnow()
        self.queue_to_asgi = asyncio.Queue()
        self.queue_from_asgi = asyncio.Queue()
        self.send_task = None
        self.scope = dict()

    async def start(self):
        asyncio.create_task(self.read_task())
        asyncio.create_task(self.write_task())

    async def read_task(self):
        while True:
            data = await self.reader.read()
            if not data:
                # This means we received an EOF. not sure how to handle this yet.
                break
            await self.data_received(data)

    async def data_received(self, data):
        """
        Receives bytes from transport and does book-keeping. Calls receive_bytes for subclass implementation.
        """
        self.bytes_received += len(data)
        self.last_received = datetime.datetime.utcnow()
        await self.receive_bytes(data)

    async def receive_bytes(self, data):
        pass

    async def write_task(self):
        while True:
            event = await self.queue_from_asgi.get()
            await self.event_received(event)

    async def event_received(self, event):
        pass

    def connection_made(self, transport):
        """
        Generates ID, registers the connection and calls the on_connection_made hook.
        """
        self.transport = transport

        # I'm paranoid about conflicting IDs no matter how impossible it's supposed to be.
        while self.uuid is None:
            maybe_id = uuid.uuid4()
            if maybe_id not in self.service.connections:
                self.uuid = maybe_id

        self.server.register_connection(self)
        self.on_connection_made(transport)

    def on_connection_made(self, transport):
        pass

    def connection_lost(self, exc):
        self.on_connection_lost(exc)
        self.server.unregister_connection(self)

    def on_connection_lost(self, exc):
        pass

    def connection_ready(self):
        pass

    def on_connection_ready(self):
        pass

    async def start_asgi(self):
        asyncio.create_task(self.app.services['asgi'].asgi_incoming(self.scope, self.queue_to_asgi.get, self.queue_from_asgi.put))

    def send_data(self, data):
        self.send_bytes(data)

    def send_bytes(self, data):
        self.bytes_sent += len(data)
        self.last_sent = datetime.datetime.now()
        self.transport.write(data)
