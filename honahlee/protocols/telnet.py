from honahlee.protocols.base import AsgiAdapterProtocol
from codecs import encode as codecs_encode
import zlib

# Much of this code has been adapted from the Evennia project https://github.com/evennia/evennia
# twisted.conch.telnet was also used for inspiration.
# Credit where credit is due.


class TCODES:
    NUL = bytes([0])
    BEL = bytes([7])
    CR = bytes([13])
    LF = bytes([10])
    SGA = bytes([3])
    NAWS = bytes([31])
    SE = bytes([240])
    NOP = bytes([241])
    DM = bytes([242])
    BRK = bytes([243])
    IP = bytes([244])
    AO = bytes([245])
    AYT = bytes([246])
    EC = bytes([247])
    EL = bytes([248])
    GA = bytes([249])
    SB = bytes([250])
    WILL = bytes([251])
    WONT = bytes([252])
    DO = bytes([253])
    DONT = bytes([254])
    IAC = bytes([255])

    # Adding more codes to the Telnet codes available.
    # MUD eXtension Protocol
    MXP = bytes([91])

    # Mud Server Status Protocol
    MSSP = bytes([70])

    # Mud Client Compression Protocol
    MCCP2 = bytes([86])
    MCCP3 = bytes([87])

    # Generic Mud Communication Protocol
    GMCP = bytes([201])

    # Mud Server Data Protocol
    MSDP = bytes([69])


# Yeah this is basically an enum.
class TSTATE:
    DATA = 0
    ESCAPED = 1
    SUBNEGOTIATION = 2
    IN_SUBNEGOTIATION = 3
    SUB_ESCAPED = 4
    COMMAND = 5
    ENDLINE = 6


class TelnetOptionState:

    def __init__(self, handler):
        self.handler = handler
        self.enabled = False
        self.negotiating = False


class TelnetOptionHandler:
    # op_code must be the byte that represents this option.
    op_code = None
    op_name = 'N\A'

    start_order = 0
    write_transform_order = 0
    read_transform_order = 0

    # If true, this OptionHandler will send a WILL <op_code> during protocol setup.
    will = False
    # if True, this optionhandler will send a DO <op>ccode> during protocol setup.
    do = False
    # For the love of pete, don't combine the above two. One or the other.

    # if true, this OptionHandler will be registered for SubNegotiation commands.
    sb = False

    def __init__(self, protocol):
        self.protocol = protocol
        self.us = TelnetOptionState(self)
        self.them = TelnetOptionState(self)

        if self.sb:
            protocol.negotiationMap[self.op_code] = self.receive_sb

    async def recv_WILL(self):

        if self.us.negotiating:
            # The client is enabling a feature on their end after we sent a DO.
            self.us.negotiating = False
            self.us.sent = None
            self.them.enabled = True
            await self.enableRemote()
        else:
            # If the above isn't true, then we are receiving a WILL from out of nowhere. That means the Remote Side
            # wants to enable. We will answer an affirmative and enable it.
            if not self.them.enabled:
                self.them.enabled = True
                await self.protocol.send_data(TCODES.DO)
                await self.enableRemote()

    async def recv_WONT(self):
        # We will not be answering this but let's see what needs doing...

        if self.us.negotiating:
            # We asked the remote party to enable this and they refused.
            self.us.negotiating = False
            await self.refusedRemote()
        else:
            # If we randomly received a WONT for a feature that we can use... we should disable this if it's enabled.
            # Else, we're going to ignore this.
            if self.them.enabled:
                self.them.enabled = False
                await self.disableRemote()

    async def recv_DO(self):
        if self.us.negotiating:
            # We asked the client if we can use this, and they said yes.
            self.us.negotiating = False
            self.us.enabled = True
            await self.enableLocal()
        else:
            # If the above isn't true, the client wants us to use this.
            if not self.us.enabled:
                self.us.enabled = True
                await self.enableLocal()

    async def recv_DONT(self):
        if self.us.negotiating:
            # Well. We wanted to use this, but they say nope...
            self.us.negotiating = False
            await self.refusedLocal()

    async def refusedLocal(self):
        pass

    async def refusedRemote(self):
        pass

    async def disableLocal(self):
        pass

    async def disableRemote(self):
        pass

    async def enableLocal(self):
        pass

    async def enableRemote(self):
        pass

    async def receive_sb(self, data):
        pass

    async def send_sb(self, data):
        await self.protocol.send_data(TCODES.IAC + TCODES.SB + self.op_code + data + TCODES.IAC + TCODES.SE)

    def read_transform(self, data):
        return data

    def write_transform(self, data):
        return data


class SGAHandler(TelnetOptionHandler):
    op_code = TCODES.SGA
    op_name = "SGA"
    will = True


class NAWSHandler(TelnetOptionHandler):
    op_code = TCODES.NAWS
    op_name = 'NAWS'
    # For some reason, official spec says that the server must open up with a DO. No SERVER WILL. Weird.
    # Why? I dunno. Ffffffing telnet.
    do = True
    sb = True

    def __init__(self, protocol):
        super().__init__(protocol)

    def receive_sb(self, data):
        if len(data) == 4:
            # NAWS is negotiated with 16bit words
            new_width = int(codecs_encode(data[0:1], "hex"), 16)
            new_height = int(codecs_encode(data[2:3], "hex"), 16)

            if new_width != self.width:
                self.change_width(new_width)
            if new_height != self.height:
                self.change_height(new_height)

    def change_width(self, new_width):
        self.protocol.protocol_flags["SCREENWIDTH"] = new_width

    def change_height(self, new_height):
        self.protocol.protocol_flags["SCREENHEIGHT"] = new_height


class TTYPEHandler(TelnetOptionHandler):
    op_code = bytes([24])
    op_name = "TTYPE"
    will = True
    sb = True

    MTTS = [
        (128, "PROXY"),
        (64, "SCREENREADER"),
        (32, "OSC_COLOR_PALETTE"),
        (16, "MOUSE_TRACKING"),
        (8, "XTERM256"),
        (4, "UTF-8"),
        (2, "VT100"),
        (1, "ANSI"),
    ]

    def __init__(self, protocol):
        super().__init__(protocol)
        self.counter = 0
        self.name_bytes = None

    def enable(self):
        self.request()

    def request(self):
        # IAC SB TTYPE SEND IAC SE
        self.send_sb(bytes([1]))

    def set_client(self, name):
        name = name.upper()
        self.protocol.protocol_flags["CLIENT_NAME"] = name

        # use name to identify support for xterm256. Many of these
        # only support after a certain version, but all support
        # it since at least 4 years. We assume recent client here for now.
        xterm256 = False
        if name.startswith("MUDLET"):
            name, version = name.split()
            name = name.strip()
            version = version.strip()
            self.protocol.protocol_flags["CLIENT_VERSION"] = version
            self.protocol.protocol_flags["CLIENT_NAME"] = name

            # supports xterm256 stably since 1.1 (2010?)
            xterm256 = version >= "1.1"
            self.protocol.protocol_flags["FORCEDENDLINE"] = False

        if name.startswith("TINTIN++"):
            self.protocol.protocol_flags["FORCEDENDLINE"] = True

        if (
                name.startswith("XTERM")
                or name.endswith("-256COLOR")
                or name
                in (
                "ATLANTIS",  # > 0.9.9.0 (aug 2009)
                "CMUD",  # > 3.04 (mar 2009)
                "KILDCLIENT",  # > 2.2.0 (sep 2005)
                "MUDLET",  # > beta 15 (sep 2009)
                "MUSHCLIENT",  # > 4.02 (apr 2007)
                "PUTTY",  # > 0.58 (apr 2005)
                "BEIP",  # > 2.00.206 (late 2009) (BeipMu)
                "POTATO",  # > 2.00 (maybe earlier)
                "TINYFUGUE",  # > 4.x (maybe earlier)
        )
        ):
            xterm256 = True

        # all clients supporting TTYPE at all seem to support ANSI
        self.protocol.protocol_flags["XTERM256"] = xterm256
        self.protocol.protocol_flags["XTERM256"] = True

    def set_capabilities(self, data):
        # this is a term capabilities flag
        term = data
        tupper = term.upper()
        # identify xterm256 based on flag
        xterm256 = (
                tupper.endswith("-256COLOR")
                or tupper.endswith("XTERM")  # Apple Terminal, old Tintin
                and not tupper.endswith("-COLOR")  # old Tintin, Putty
        )
        if xterm256:
            self.protocol.protocol_flags["ANSI"] = True
            self.protocol.protocol_flags["XTERM256"] = xterm256
        self.protocol.protocol_flags["TERM"] = term

    def set_mtts(self, data):
        # the MTTS bitstring identifying term capabilities
        if data.startswith("MTTS"):
            option = data[4:].strip()

            if option.isdigit():
                # a number - determine the actual capabilities
                option = int(option)
                support = dict(
                    (capability, True) for bitval, capability in self.MTTS if option & bitval > 0
                )
                self.protocol.protocol_flags.update(support)
            else:
                # some clients send erroneous MTTS as a string. Add directly.
                self.protocol.protocol_flags[option.upper()] = True

    def receive_sb(self, data):
        if data[0] != bytes([0]):
            # Received a malformed TTYPE answer. Let's ignore it for now.
            return

        # slice off that IS. we don't need it.
        data = data[1:]

        if self.counter == 0:
            # This is the first time we're receiving a TTYPE IS.
            client = data.decode("utf-8", errors='ignore')
            self.set_client(client)
            self.name_bytes = data
            self.counter += 1
            # Request round 2 of our data!
            self.request()
            return

        if self.counter == 1:
            if data == self.name_bytes:
                # Some clients don't support giving further information. In that case, there's nothing
                # more for TTYPE to do.
                return
            self.set_capabilities(data)
            self.counter += 1
            self.request()
            return

        if self.counter == 2:
            self.set_mtts(data)
            self.counter += 1
            return


class MCCP2Handler(TelnetOptionHandler):
    """
    When MCCP2 is enabled, all of our outgoing bytes will be mccp2 compressed.
    """
    op_code = bytes([86])
    op_name = 'MCCP2'

    def enable(self):
        self.send_sb(bytes([]))
        self.enable_compression()

    def enable_compression(self):
        self.protocol.mccp2 = zlib.compressobj(9)
        self.protocol._write = self.protocol._write_mccp2

    def disable(self):
        self.disable_compression()

    def disable_compression(self):
        self.protocol._write = self.protocol._write_plain
        self.protocol.mccp2 = None


class MCCP3Handler(TelnetOptionHandler):
    op_code = bytes([87])
    op_name = 'MCCP3'

    def receive_sb(self, data):
        # MCCP3 can only be sending us one thing (IAC SB MCCP3 IAC SE), so we're gonna ignore the details.
        if not data:
            self.enable_compression()

    def enable_compression(self):
        self.protocol.mccp3 = zlib.decompressobj(9)
        self.protocol.dataReceived = self.protocol._dataReceived_mccp3

    def disable(self):
        self.disable_compression()

    def disable_compression(self):
        self.protocol.dataReceived = self.protocol._dataReceived_plain
        self.protocol.mccp3 = None


class MSSPHandler(TelnetOptionHandler):
    """
    It is the responsibility of the factory to report Mud Server Status Protocol data.
    """
    op_code = bytes([70])
    op_name = "MSSP"

    will = True

    def enable(self):
        response = None
        try:
            # On the off-chance that specific MSSP crawlers should be blocked, pass the protocol so the method
            # has a way to know who's asking.
            response = self.protocol.factory.generate_mssp_data(self.protocol)
        except Exception as e:
            pass
        if response:
            # this is not finished - still need to format response properly
            # self.send_sb(response)
            pass


class TelnetAsgiProtocol(AsgiAdapterProtocol):
    asgi_type = 'telnet'


    default_protocol_flags = {
        "ENCODING": "ascii",
        "SCREENREADER": False,
        "OSC_COLOR_PALETTE": False,
        "MOUSE_TRACKING": False,
        "PROXY": False,
        "UTF-8": False,
        "VT100": False,
        "RAW": False,
        "NOCOLOR": False,
        "ANSI": False,
        "XTERM256": False,
        "CLIENT_NAME": "UNKNOWN",
        "CLIENT_VERSION": "UNKNOWN",
        "SCREENWIDTH": 78,
        "SCREENHEIGHT": 24,
        "GMCP": False,
        "MXP": False,
        "MCCP2": False,
        "MCCP3": False,
        "TTYPE": False,
        "NAWS": False,
        "SGA": False,
        "LINEMODE": False,
        "FORCEDENDLINE": False,
    }

    handler_classes = [MCCP2Handler, MCCP3Handler, SGAHandler, NAWSHandler, TTYPEHandler, MSSPHandler]

    def __init__(self, reader, writer, server, application):
        super().__init__(reader, writer, server, application)

        self.data_buffer = []
        self.command_list = []

        self.telnet_state = TSTATE.DATA

        # If handlers want to do read/write-transforms on outgoing data, they'll be stored here and sorted
        # by their property.
        self.reader_transforms = []
        self.writer_transforms = []

        # These two handle when we're dealing with IAC WILL/WONT/DO/DONT and IAC SB <code>, storing data until it's
        # needed.
        self.iac_command = bytes([0])
        self.negotiate_code = bytes([0])
        self.negotiate_buffer = []

        self.handler_codes = dict()
        self.handler_names = dict()

        for h_class in self.handler_classes:
            handler = h_class(self)
            self.handler_codes[h_class.op_code] = handler
            self.handler_names[h_class.op_name] = handler

    def add_read_transform(self, handler):
        if handler not in self.reader_transforms:
            self.reader_transforms.append(handler)
            self.sort_read_transform()

    def remove_read_transform(self, handler):
        if handler in self.reader_transforms:
            self.reader_transforms.remove(handler)
            self.sort_read_transform()

    def add_write_transform(self, handler):
        if handler not in self.writer_transforms:
            self.writer_transforms.append(handler)
            self.sort_write_transform()

    def remove_write_transform(self, handler):
        if handler in self.writer_transforms:
            self.writer_transforms.remove(handler)
            self.sort_write_transform()

    def sort_read_transform(self):
        self.reader_transforms.sort(key=lambda h: h.read_transform_order)

    def sort_write_transform(self):
        self.writer_transforms.sort(key=lambda h: h.write_transform_order)

    async def handle_reader(self, data):
        """
        Iterate over all bytes.

        This is largely shamelessly ripped from twisted.conch.telnet
        """
        app_data_buffer = []

        # This is mostly for MCCP3.
        for handler in self.reader_transforms:
            data = handler.read_transform(data)

        for b in [bytes([i]) for i in data]:

            if self.telnet_state == TSTATE.DATA:
                if b == TCODES.IAC:
                    self.telnet_state = TSTATE.ESCAPED
                elif b == b'\r':
                    self.telnet_state = TSTATE.ENDLINE
                else:
                    app_data_buffer.append(b)
            elif self.telnet_state == TSTATE.ESCAPED:
                if b == TCODES.IAC:
                    app_data_buffer.append(b)
                    self.telnet_state = TSTATE.DATA
                elif b == TCODES.SB:
                    self.telnet_state = TSTATE.SUBNEGOTIATION
                    self.negotiate_buffer = []
                elif b in (TCODES.NOP, TCODES.DM, TCODES.BRK, TCODES.IP, TCODES.AO, TCODES.AYT, TCODES.EC, TCODES.EL, TCODES.GA):
                    self.telnet_state = TSTATE.DATA
                    if app_data_buffer:
                        await self.parse_application_data(b''.join(app_data_buffer))
                        del app_data_buffer[:]
                    await self.execute_iac_command(b, None)
                elif b in (TCODES.WILL, TCODES.WONT, TCODES.DO, TCODES.DONT):
                    self.telnet_state = TSTATE.COMMAND
                    self.iac_command = b
                else:
                    raise ValueError("Stumped", b)
            elif self.telnet_state == 'command':
                self.telnet_state = 'data'
                if app_data_buffer:
                    await self.parse_application_data(b''.join(app_data_buffer))
                    del app_data_buffer[:]
                await self.execute_iac_command(self.iac_command, b)
                self.iac_command = bytes([0])
            elif self.telnet_state == TSTATE.ENDLINE:
                self.telnet_state = TSTATE.DATA
                if b == b'\n':
                    app_data_buffer.append(b'\n')
                elif b == b'\0':
                    app_data_buffer.append(b'\r')
                elif b == TCODES.IAC:
                    # IAC isn't really allowed after \r, according to the
                    # RFC, but handling it this way is less surprising than
                    # delivering the IAC to the app as application data.
                    # The purpose of the restriction is to allow terminals
                    # to unambiguously interpret the behavior of the CR
                    # after reading only one more byte.  CR LF is supposed
                    # to mean one thing (cursor to next line, first column),
                    # CR NUL another (cursor to first column).  Absent the
                    # NUL, it still makes sense to interpret this as CR and
                    # then apply all the usual interpretation to the IAC.
                    app_data_buffer.append(b'\r')
                    self.telnet_state = TSTATE.ESCAPED
                else:
                    app_data_buffer.append(b'\r' + b)
            elif self.telnet_state == TSTATE.SUBNEGOTIATION:
                if b == TCODES.IAC:
                    self.telnet_state = TSTATE.SUB_ESCAPED
                else:
                    self.negotiate_buffer.append(b)
            elif self.telnet_state == TSTATE.SUB_ESCAPED:
                if b == TCODES.SE:
                    self.telnet_state = TSTATE.DATA
                    if app_data_buffer:
                        await self.parse_application_data(b''.join(app_data_buffer))
                    await self.sub_negotiate(self.negotiate_code, self.negotiate_buffer)
                    self.negotiate_code = bytes([0])
                    self.negotiate_buffer.clear()
                else:
                    self.telnet_state = TSTATE.SUBNEGOTIATION
                    self.negotiate_buffer.append(b)
            else:
                raise ValueError("How'd you do this?")

            if app_data_buffer:
                await self.parse_application_data(b''.join(app_data_buffer))

    async def sub_negotiate(self, op_code, data):
        if (handler := self.handler_codes.get(op_code, None)):
            await handler.receive_sb(data)

    async def execute_iac_command(self, command, op_code):
        if op_code is None:
            if command == TCODES.AYT:
                # Let's respond to 'ARE YOU THERE' with 'NOP'. Kind of a Keepalive
                await self.send_data(TCODES.NOP)
            return

        if (handler := self.handler_codes.get(op_code, None)):
            if command == TCODES.WILL:
                await handler.recv_WILL()
            if command == TCODES.WONT:
                await handler.recv_WONT()
            if command == TCODES.DO:
                await handler.recv_DO()
            if command == TCODES.DONT:
                await handler.recv_DONT()

    async def parse_application_data(self, data):
        """
        This is called by super().dataReceived() and it receives a pile of bytes.
        This will never contain IAC-escaped sequences, but may contain other special
        characters/symbols/bytes.
        """
        # First, append all the new data to our app buffer.

        for b in data:

            if b in (TCODES.NUL, TCODES.NOP):
                # Ignoring this ancient keepalive
                # convert it to the IDLE COMMAND here...
                await self.user_command(b"IDLE")
                continue
            if b == TCODES.LF:
                await self.user_command(b''.join(self.data_buffer))
                self.data_buffer.clear()
                continue

            # Nothing else stands out? Append the data to data buffer...
            self.data_buffer.append(b)

    async def user_command(self, command):
        """
        Decodes user-entered command into preferred style, such as UTF-8.

        Args:
            command (byte string): The user-entered command, minus terminating CRLF
        """
        decoded = command.decode("utf-8", errors='ignore')
        event = {
            "type": "telnet.line",
            "line": decoded
        }
        await self.to_app.put(event)

    async def send_data(self, data):
        """
        Run transforms on all outgoing data before sending to transport.

        Args:
            data (bytearray): The data being sent.

        """
        for handler in self.writer_transforms:
            data = handler.write_transform(data)
        await self.write_data(data)
