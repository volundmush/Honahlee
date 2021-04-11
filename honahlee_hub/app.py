import datetime
from honahlee.core import Application as BaseApplication

from mudlink.mudconnection import AbstractConnection


class LinkedConnection(AbstractConnection):

    def __init__(self, app, data):
        super().__init__()
        self.app = app
        self.update(data)

    def update(self, data):
        self.capabilities.__dict__.update(data.pop("capabilities"))
        self.created = datetime.datetime.utcfromtimestamp(data.pop("created"))
        self.__dict__.update(data)


class Application(BaseApplication):

    def __init__(self, config):
        super().__init__(config)
        self.connections = dict()

    async def joined(self, session, details):
        session.subscribe(self.portal_client_connected, "honahlee.portal.events.client_connected")
        session.subscribe(self.portal_client_command, "honahlee.portal.events.client_command")
        session.subscribe(self.portal_client_update, "honahlee.portal.events.client_update")
        session.subscribe(self.portal_client_ready, "honahlee.portal.events.client_ready")
        clients = await session.call("honahlee.portal.rpc.all_clients")
        for v in clients.values():
            self.link_client(v)

    def portal_client_connected(self, *args, **kwargs):
        self.link_client(kwargs)

    def portal_client_command(self, *args, **kwargs):
        if (conn := self.connections.get(kwargs.get("name", None), None)):
            print(f"HUB GOT COMMAND FOR {conn.name}: {kwargs.get('command')}")
        else:
            print(f"HUB GOT COMMAND FOR UNKNOWN {kwargs.get('name')}: {kwargs.get('command')}")

    def portal_client_ready(self, *args, **kwargs):
        if (conn := self.connections.get(kwargs.get("name", None), None)):
            conn.update(kwargs)
            print(f"HUB CONNECTION READY: {conn.export()}")
        else:
            print(f"HUB RECEIVED UNKNOWN READY: {kwargs}")

    def portal_client_update(self, *args, **kwargs):
        if (conn := self.connections.get(kwargs.get("name", None), None)):
            conn.update(kwargs)
            print(f"HUB CONNECTION UPDATED: {conn.export()}")
        else:
            print(f"HUB RECEIVED UNKNOWN UPDATE: {kwargs}")

    def link_client(self, data):
        name = data['name']
        if (conn := self.connections.get(name, None)):
            conn.update(data)
        else:
            conn = LinkedConnection(self, data)
            self.connections[name] = conn