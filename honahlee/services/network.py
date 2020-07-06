from honahlee.core import BaseService
from honahlee.utils.misc import import_from_module
from twisted.internet.protocol import ServerFactory
from twisted.internet import ssl


class HonahleeServerFactory(ServerFactory):

    def __init__(self, service, name, address, port, protocol, tls):
        self.service = service
        self.name = name
        self.address = address
        self.port = port
        self.protocol = protocol
        self.tls = tls
        self.listener = None


class NetworkService(BaseService):
    setup_order = -900

    def __init__(self, app):
        super().__init__(app)
        self.games = dict()
        self.server_classes = dict()
        self.servers = dict()
        self.protocol_classes = dict()
        self.connections = dict()
        self.ssl_context = None

    def register_server_class(self, name, server_class):
        self.server_classes[name] = server_class

    def register_protocol_class(self, name, protocol_class):
        self.protocol_classes[name] = protocol_class

    def create_server(self, name, address, port, server_class, protocol_class, tls):
        if name in self.servers:
            raise ValueError("That name conflicts with an existing server!")
        if not (srv_class := self.server_classes.get(server_class, None)):
            raise ValueError(f"Server Class {server_class} has not been registered!")
        if not (prot_class := self.protocol_classes.get(protocol_class, None)):
            raise ValueError(f"Protocol Class {protocol_class} has not been registered!")
        if tls and not self.ssl_context:
            raise ValueError("TLS is not properly configured. Cannot start TLS server.")
        new_server = srv_class(self, name, address, port, prot_class, tls)
        self.servers[name] = new_server
        from twisted.internet import reactor
        if tls:
            pass
        else:
            new_server.listener = reactor.listenTCP(port, new_server, interface=address)
        return new_server

    def register_connection(self, conn):
        self.connections[conn.uuid] = conn

    def unregister_connection(self, conn):
        del self.connections[conn.uuid]

    def setup(self):
        for k, v in self.app.settings.SERVER_CLASSES.items():
            srv_class = import_from_module(v)
            self.register_server_class(k, srv_class)
        for k, v in self.app.settings.PROTOCOL_CLASSES.items():
            prot_class = import_from_module(v)
            self.register_protocol_class(k, prot_class)
        # do TLS init down here...

        for k, v in self.app.settings.SERVERS.items():
            self.create_server(k, self.app.settings.INTERFACE, v['port'], v['server_class'], v['protocol_class'], v['tls'])

    def start(self):
        for k, v in self.servers.items():
            pass
            #v.listener.startListening()
