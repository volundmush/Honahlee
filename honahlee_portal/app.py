from honahlee.core import Application as BaseApplication, BaseService
from mudlink.mudlink import MudLinkManager
import asyncio
import json
from mudlink.telnet import TelnetOutMessage


class MudLinkService(MudLinkManager, BaseService):
    name = 'mudlink'

    def __init__(self, app):
        MudLinkManager.__init__(self)
        BaseService.__init__(self, app)

    async def start(self):
        self.listen()
        await self.run()


class Application(BaseApplication):

    def __init__(self, config):
        super().__init__(config)
        self.mudlink = None

    async def setup(self):
        await super().setup()
        self.mudlink = self.services['mudlink']
        self.mudlink.ssl_contexts = self.config.tls_contexts
        self.mudlink.interfaces = self.config.interfaces
        self.mudlink.on_connect_cb = self.mudlink_on_connect
        for k, v in self.config.listeners.items():
            self.mudlink.register_listener(k, v["interface"], v["port"], v["protocol"], ssl_context=v.get("tls", None))

    def mudlink_on_connect(self, conn):
        conn.on_command_cb = self.mudlink_on_command
        conn.on_disconnect_cb = self.mudlink_on_disconnect
        conn.on_oob_cb = self.mudlink_on_oob
        conn.on_ready_cb = self.mudlink_on_ready
        conn.on_update_cb = self.mudlink_on_update

        if self.session:
            self.session.publish("honahlee.portal.events.client_connected", **conn.export())

    def mudlink_on_disconnect(self, conn):
        if self.session:
            self.session.publish("honahlee.portal.events.client_disconnected", **{"name": conn.name})

    def mudlink_on_command(self, conn, command):
        if self.session:
            self.session.publish("honahlee.portal.events.client_command", **{"name": conn.name, "command": command.decode()})

    def mudlink_on_oob(self, conn, data):
        if self.session:
            self.session.publish("honahlee.portal.events.client_oob", **{"name": conn.name, "oob": data})

    def mudlink_on_ready(self, conn):
        if self.session:
            self.session.publish("honahlee.portal.events.client_ready", **conn.export())

    def mudlink_on_update(self, conn):
        print(f"{conn} called mudlink_on_update")
        if self.session:
            self.session.publish("honahlee.portal.events.client_update", **conn.export())

    def rpc_all_clients(self, *args, **kwargs):
        return {conn.name: conn.export() for conn in self.mudlink.connections.values()}

    def rpc_client_text(self, *args, **kwargs):
        pass

    def rpc_client_prompt(self, *args, **kwargs):
        pass

    def rpc_client_oob(self, *args, **kwargs):
        pass

    def rpc_client_mssp(self, *args, **kwargs):
        pass

    def rpc_client_setdata(self, *args, **kwargs):
        pass

    def rpc_client_getdata(self, *args, **kwargs):
        pass

    def rpc_client_close(self, *args, **kwargs):
        pass

    def joined(self, session, details):
        super().joined(session, details)
        session.register(self.rpc_all_clients, 'honahlee.portal.rpc.all_clients')
        session.register(self.rpc_client_text, "honahlee.portal.rpc.client_text")
        session.register(self.rpc_client_prompt, "honahlee.portal.rpc.client_prompt")
        session.register(self.rpc_client_oob, "honahlee.portal.rpc.client_oob")
        session.register(self.rpc_client_mssp, "honahlee.portal.rpc.client_mssp")
        session.register(self.rpc_client_setdata, "honahlee.portal.rpc.client_setdata")
        session.register(self.rpc_client_getdata, "honahlee.portal.rpc.client_getdata")
        session.register(self.rpc_client_close, "honahlee.portal.rpc.client_close")
