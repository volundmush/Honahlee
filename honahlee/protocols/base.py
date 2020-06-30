import asyncio
import uuid
import datetime


class BaseProtocol(asyncio.Protocol):
    """
    This Protocol is abstract.
    """
    protocol_name = 'base'

    def __init__(self, server):
        self.server = server
        self.service = server.service
        self.app = self.service.app
        self.transport = None
        self.client = None
        self.uuid = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self.creation_datetime = datetime.datetime.utcnow()
        self.last_received = datetime.datetime.utcnow()
        self.last_sent = datetime.datetime.utcnow()

    def data_received(self, data):
        """
        Receives bytes from transport and does book-keeping. Calls receive_bytes for subclass implementation.
        """
        self.bytes_received += len(data)
        self.last_received = datetime.datetime.utcnow()
        self.receive_bytes(data)

    def receive_bytes(self, data):
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

    def send_data(self, data):
        self.send_bytes(data)

    def send_bytes(self, data):
        self.bytes_sent += len(data)
        self.last_sent = datetime.datetime.now()
        self.transport.write(data)
