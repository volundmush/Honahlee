import asyncio
import datetime


class AsgiAdapterProtocol:
    """
    A base class for creating new Protocols that are meant to connect to an ASGI Application.
    This is for streaming / sustained connections, like Telnet and WebSockets. It assumes the ASGI application will not
    be returning anytime soon.
    """
    base_asgi_dict = {'type': None, 'asgi': {'spec_version': '2.1', 'version': '3.0'},
                      'client': None,  # Fill this out with a tuple of ADDR, Port
                      'server': None,  # Same as client.
                      "bytes_sent": 0,
                      "bytes_received": 0,
                      "connection_date": None,
                      "headers": [] # technically for HTTP/WebSockets. having this allows Django to work with Telnet
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
        self.reader_task = asyncio.create_task(self.run_reader())
        self.events_task = asyncio.create_task(self.run_events())

    def setup_scope(self):
        self.scope["type"] = self.asgi_type
        self.scope["server"] = (self.server.address, self.server.port)
        self.scope["connection_date"] = datetime.datetime.utcnow()

    async def generate_connect(self):
        """
        This overloadable method is meant to send a 'connect' type event to the to_app queue before entering the ASGI
        application.
        """
        pass

    async def asgi(self):
        """
        This is the 'entry point' into this ASGI application. It makes ASGI aware of this connection and kicks off the
        connection. Call this after all handshakes and low level protocol setup.
        """
        await self.generate_connect()
        self.app_task = asyncio.create_task(self.application(self.scope, self.to_app.get, self.from_app.put))

    async def run_reader(self):
        """
        A loop that continuously checks for events coming in from the ASGI reader.
        """
        while True:
            data = await self.reader.read(self.read_buffer)
            if data:
                await self.handle_reader(data)
                self.scope["bytes_received"] += len(data)

    async def run_events(self):
        while True:
            event = await self.from_app.get()
            await self.handle_event(event)

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
        self.scope["bytes_sent"] += len(data)

    async def handle_reader(self, data):
        """
        This method decides what to do with the message sent to it from the reader. This should be in chunks of up to
        1 to <read_buffer> size.

        Args:
            data (bytearray): Raw data from TCP/TLS.
        """
        pass
