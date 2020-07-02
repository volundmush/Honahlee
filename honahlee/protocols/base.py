import asyncio


class ASGIProtocol:

    def __init__(self, server):
        self.server = server
        self.scope = None
        self.forward_scope = dict()
        self.forward_reader = asyncio.Queue()
        self.forward_writer = asyncio.Queue()
        self.reader = None
        self.writer = None
        self.reader_task = None
        self.writer_task = None
        self.forward_reader_task = None
        self.forward_writer_task = None

    async def accept_asgi(self, scope, reader, writer):
        """
        This is the 'entry point' into this ASGI application.
        """
        self.scope = scope
        self.reader = reader
        self.writer = writer
        await self.setup()
        self.reader_task = asyncio.create_task(self.run_reader())
        self.writer_task = asyncio.create_task(self.run_forward_writer())

    async def setup(self):
        """
        Customizable hook meant to setup this object once accept_asgi is called.
        """

    async def run_reader(self):
        """
        A loop that continuously checks for events coming in from the ASGI reader.
        """
        while True:
            data = await self.reader.read(4096)
            if data:
                await self.handle_reader(data)

    async def handle_reader(self, data):
        """
        This method decides what to do with the message sent to it from the reader.
        """
        pass

    async def run_forward_writer(self):
        """
        Loop that continuously checks for events sent from the next level 'up'.
        """
        while True:
            data = await self.forward_writer.get()
            if data:
                await self.handle_forward_writer(data)

    async def handle_forward_writer(self, data):
        """
        Decode events sent from the next level up... and do something with them.
        """
