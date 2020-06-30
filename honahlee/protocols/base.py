import asyncio
import uuid


class BaseProtocol(asyncio.Protocol):

    def __init__(self, server):
        self.server = server
        self.service = server.service
        self.app = self.service.app
        self.transport = None
        self.client = None
        self.uuid = None

    def data_received(self, data):
        self.transport.write(data)
        self.client.process_command(data.decode())

    def connection_made(self, transport):
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

    def register_client(self, client):
        self.client = client
        self.on_register_client(client)

    def on_register_client(self, client):
        pass

    def send_bytes(self, data):
        self.final_send_bytes(data)

    def final_send_bytes(self, data):
        self.transport.write(data)
