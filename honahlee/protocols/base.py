import asyncio
import datetime

from asgiref.compatibility import is_double_callable, double_to_single_callable
from channels.consumer import AsyncConsumer, StopConsumer
from channels.auth import login, logout

class AsgiAdapterProtocol:
    """
    A base class for creating new Protocols that are meant to connect to an ASGI Application.
    This is for streaming / sustained connections, like Telnet and WebSockets. It assumes the ASGI application will not
    be returning anytime soon.
    """
    base_asgi_dict = {'type': None, 'asgi': {'spec_version': '2.1', 'version': '3.0'},
                      'client': None,  # Fill this out with a tuple of ADDR, Port
                      'server': None,  # Same as client.
                      "connection_date": None,
                      "headers": [],  # technically for HTTP/WebSockets. having this allows Django to work with Telnet
                      }

    base_client_dict = {"capabilities": {},
                        "name": "Unknown",
                        "version": "Unknown",
                        "terminal": "Unknown",
                        "width": 78,
                        "height": 24,
                        "options": {},
                        "bytes_sent": 0,
                        "bytes_received": 0,
                        }

    base_client_capabilities_dict = {
        "ansi": False,
        "xterm256": False,
        "utf8": False,
        "oob": False
    }

    base_client_options_dict = {
        "screenreader": False,
        "nocolor": False
    }

    # The 'type' of this protocol that will be shown in ASGI.
    asgi_type = None
    # The maximum amount of bytes that will be read from a socket at once.
    read_buffer = 4096

    # Flow control for outgoing data. Only useful if drain is enabled.
    write_low_water = 1024
    write_high_water = 1024 * 40

    # Use drain. This will cause outgoing writes to be paused until the transport is ready to accept more data.
    # This mechanism prevents a massive buffer buildup on the outgoing socket.
    drain = False

    def __init__(self, reader, writer, server, application):
        self.server = server
        self.bytes_sent = 0
        self.bytes_received = 0
        self.application = application
        self.scope = dict(self.base_asgi_dict)
        self.to_app = asyncio.Queue()
        self.from_app = asyncio.Queue()
        self.reader = reader
        self.writer = writer
        self.writer.transport.set_write_buffer_limits(high=self.write_high_water, low=self.write_low_water)
        self.reader_task = None
        self.events_task = None
        self.from_app_task = None
        self.app_task = None
        self.setup_scope()

    async def start(self):
        await self.generate_connect()
        self.reader_task = asyncio.create_task(self.run_reader())
        self.events_task = asyncio.create_task(self.run_events())
        await self.start_negotiation()
        # When negotiation is over, we are actually closing up shop...
        if self.reader_task:
            self.reader_task.cancel()
        self.events_task.cancel()

    async def app_reader(self):
        """
        This ensures that the Queue tasks will be accounted for when Consumers use this.
        """
        msg = await self.to_app.get()
        self.to_app.task_done()
        return msg

    async def start_negotiation(self):
        pass

    async def stop(self):
        pass

    def setup_scope(self):
        self.scope["type"] = self.asgi_type
        self.scope["server"] = (self.server.address, self.server.port)
        self.scope["connection_date"] = datetime.datetime.utcnow()
        self.scope["game_client"] = self.base_client_dict.copy()
        self.scope["game_client"]["capabilities"] = self.base_client_capabilities_dict.copy()
        self.scope["game_client"]["options"] = self.base_client_options_dict.copy()

    async def generate_connect(self):
        """
        This overloadable method is meant to send a 'connect' type event to the to_app queue before entering the ASGI
        application.
        """
        await self.to_app.put({
            'type': f"{self.asgi_type}.connect"
        })

    async def asgi(self):
        """
        This is the 'entry point' into this ASGI application. It makes ASGI aware of this connection and kicks off the
        connection. Call this after all handshakes and low level protocol setup.
        """
        # Sometimes an ASGI application is old style, so we'll wrap it to 3.0 if need be.
        app = self.application
        if is_double_callable(app):
            app = double_to_single_callable(app)
        # asyncio.get_event_loop().create_task(app(self.scope, self.app_reader, self.from_app.put))
        await app(self.scope, self.app_reader, self.from_app.put)

    async def run_reader(self):
        """
        A loop that continuously checks for events coming in from the ASGI reader.
        """
        while True:
            data = await self.reader.read(self.read_buffer)
            if data:
                await self.handle_reader(data)
                self.scope["game_client"]["bytes_received"] += len(data)
            else:
                # The only reason data would be false is if an EOF is received...
                await self.to_app.put({
                    'type': f"{self.asgi_type}.disconnect",
                    'reason': "EOF"
                })
                break
        self.reader_task.cancel()

    async def run_events(self):
        while True:
            event = await self.from_app.get()
            await self.handle_event(event)
            self.from_app.task_done()

    async def handle_event(self, event):
        """
        This receives events from the ASGI Application. This generally means this Event should be analyzed and
        turned into something that can be sent to the client. That's not necessarily the case though.

        Args:
            event (dict): A protocol-specification dictionary.
        """
        pass

    async def write_data(self, data):
        """
        Writes outgoing bytes to transport, optionally waiting until it is safe/smart to do so if drain is enabled.

        Args:
            data (bytearray): The outgoing bytes.
        """
        if self.drain:
            await self.writer.drain()
        self.writer.write(data)
        self.scope["game_client"]["bytes_sent"] += len(data)

    async def handle_reader(self, data):
        """
        This method decides what to do with the message sent to it from the reader. This should be in chunks of up to
        1 to <read_buffer> size.

        Args:
            data (bytearray): Raw data from TCP/TLS.
        """
        pass


class AsyncGameConsumerMixin:
    """
    This is a class meant to be added to any Async Consumer that's supposed to be interacting
    as a Game Client.
    """
    app = None

    async def game_login(self, account):
        """
        Log this consumer in to the game via Django.

        Args:
            account (User): The Django User account to bind to this Consumer.
        """
        await login(self.scope, account)

    async def game_close(self, reason):
        """
        Call all cleanup routines and close this consumer. This can be triggered by either the client
        or the server.

        Args:
            reason (str): The reason for this closing.
        """
        raise StopConsumer(reason)

    async def game_input(self, cmd, *args, **kwargs):
        """
        Processes input from players in Inputfunc Format. See Evennia specs for details.
        """
        if (func := self.app.input_funcs.get(cmd, None)):
            await func(self, cmd, *args, **kwargs)

    async def game_output(self, cmd, *args, **kwargs):
        """
        Processes output from Honahlee and game servegrs, sends to players.
        """
        if (func := self.app.output_funcs.get(cmd, None)):
            await func(self, cmd, *args, **kwargs)

    async def game_link(self, game):
        pass

    async def game_unlink(self, game):
        pass

    async def game_connect(self):
        pass
