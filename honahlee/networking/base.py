import asyncio
import uuid


class GameClient:

    def __init__(self, client_id, protocol, manager):
        self.client_id = client_id
        self.manager = manager
        self.protocol = protocol
        protocol.register_client(self)

    def execute_command(self, command):
        self.protocol.send_bytes(command)


class GameClientProtocol(asyncio.Protocol):
    manager = None

    def __init__(self):
        self.transport = None
        self.client = None

    def data_received(self, data):
        self.transport.write(data)
        self.client.process_command(data.decode())

    def connection_made(self, transport):
        self.transport = transport
        self.manager.setup_client(self)
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


class NetworkManager:

    def __init__(self, app):
        self.app = app
        self.games = dict()
        self.servers = dict()
        self.protocols = dict()
        self.clients = dict()
        self.ssl_context = None

    def register_protocol(self, name, protocol):
        protocol.manager = self
        self.protocols[name] = protocol

    async def create_server(self, name, address, port, protocol, tls):
        prot = self.protocols.get(protocol, None)
        loop = asyncio.get_running_loop()
        ssl = None
        if self.ssl_context and tls:
            ssl = self.ssl_context
        new_server = await loop.create_server(lambda: prot(), host=address, port=port, ssl=ssl)
        self.servers[name] = new_server
        return new_server

    def setup_client(self, protocol):
        good_id = None
        while good_id is None:
            maybe_id = uuid.uuid4()
            if maybe_id not in self.clients:
                good_id = maybe_id
        self.clients[good_id] = GameClient(good_id, protocol, self)
