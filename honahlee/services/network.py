import asyncio
from honahlee.core import BaseService


class HonahleeNetworkBase:
    app = None

    def __init__(self, service, name, address, port, protocol, tls):
        self.service = service
        self.name = name
        self.address = address
        self.port = port
        self.protocol = protocol
        self.tls = tls


class HonahleeServer(HonahleeNetworkBase):

    def __init__(self, service, name, address, port, protocol, tls):
        super().__init__(service, name, address, port, protocol, tls)
        self.server = None
        self.task = None

    async def accept(self, reader, writer):
        asgi = self.service.app.services['web'].asgi_app
        new_protocol = self.protocol(reader, writer, self, asgi)
        # asyncio.get_event_loop().create_task(new_protocol.start())
        await new_protocol.start()

    async def start(self):
        ssl = self.service.ssl_context if self.tls else None
        self.server = asyncio.start_server(self.accept, host=self.address, port=self.port, ssl=ssl)
        self.task = asyncio.get_event_loop().create_task(self.server)

    async def stop(self):
        if self.server:
            self.server.stop()


class ServerService(BaseService):
    setup_order = -900

    def __init__(self):
        self.servers = dict()
        self.connections = dict()

    def create_server(self, name, address, port, server_class, protocol_class, tls):
        if name in self.servers:
            raise ValueError("That name conflicts with an existing server!")
        if not (srv_class := self.app.classes['servers'].get(server_class, None)):
            raise ValueError(f"Server Class {server_class} has not been registered!")
        if not (prot_class := self.app.classes['protocols'].get(protocol_class, None)):
            raise ValueError(f"Protocol Class {protocol_class} has not been registered!")
        tls_context = None
        if tls and not (tls_context := self.app.tls.get(tls, None)):
            raise ValueError(f"TLS is not properly configured. No context for {tls}! Cannot start TLS server.")
        new_server = srv_class(self, name, address, port, prot_class, tls_context)
        self.servers[name] = new_server

    def register_connection(self, conn):
        new_uuid = self.app.fresh_uuid4(self.servers.keys())
        conn.conn_id = new_uuid
        self.connections[conn.conn_id] = conn

    def unregister_connection(self, conn):
        del self.connections[conn.conn_id]

    async def setup(self):

        for k, v in self.app.config.servers.items():
            self.create_server(k, self.app.config.interfaces[v['interface']], v['port'], v['server_class'], v['protocol_class'],
                               v['tls'])

    async def start(self):
        for k, v in self.servers.items():
            await v.start()


class HonahleeClient(HonahleeNetworkBase):

    def __init__(self, service, name, address, port, protocol, tls):
        super().__init__(service, name, address, port, protocol, tls)
        self.client = None
        self.task = None

    async def accept(self, reader, writer):
        pass

    async def start(self):
        pass

    async def stop(self):
        if self.client:
            self.client.stop()


class ClientService(BaseService):

    def __init__(self):
        self.clients = dict()
        self.connections = dict()
