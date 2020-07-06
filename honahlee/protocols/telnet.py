from twisted.conch import telnet as t
from twisted.python.compat import iterbytes
from codecs import encode as codecs_encode
import zlib

# Much of this code has been adapted from the Evennia project https://github.com/evennia/evennia
# Credit where credit is due.


class TelnetOptionHandler:
    # op_code must be the byte that represents this option.
    op_code = None
    op_name = 'N\A'

    order = 0

    # If true, this OptionHandler will send a WILL <op_code> during protocol setup.
    will = False
    # if True, this optionhandler will send a DO <op>ccode> during protocol setup.
    do = False
    # For the love of pete, don't combine the above two. One or the other.

    # if true, this OptionHandler will be registered for SubNegotiation commands.
    sb = False

    def __init__(self, protocol):
        self.protocol = protocol
        self.enabled = False
        self.sent = 0
        if self.sb:
            protocol.negotiationMap[self.op_code] = self.receive_sb
        self.state = protocol.getOptionState(self.op_code)

    def start(self):
        if self.will:
            d = self.protocol.will(self.op_code)
            d.addCallbacks(self.will_result, self.will_result)
        if self.do:
            d = self.protocol.do(self.op_code)
            d.addCallbacks(self.do_result, self.do_result)

    def will_result(self, answer):
        # Do not simplify this. 'answer' might be an Exception...
        if answer == True:
            self.enableLocal()

    def do_result(self, answer):
        if answer == True:
            self.enableLocal()

    def disableLocal(self):
        self.protocol.protocol_flags[self.op_name] = False
        self.disable()

    def disableRemote(self):
        self.protocol.protocol_flags[self.op_name] = False
        self.disable()

    def disable(self):
        pass

    def enableLocal(self):
        self.protocol.protocol_flags[self.op_name] = True
        self.enable()

    def enableRemote(self):
        self.protocol.protocol_flags[self.op_name] = True
        self.enable()

    def enable(self):
        pass

    def receive_sb(self, data):
        pass

    def send_sb(self, data):
        self.protocol._write(t.IAC + t.SB + self.op_code + data + t.IAC + t.SE)


class SGAHandler(TelnetOptionHandler):
    op_code = t.SGA
    op_name = "SGA"
    will = True


class MXPHandler(TelnetOptionHandler):
    op_code = bytes([91])
    op_name = 'MXP'


class NAWSHandler(TelnetOptionHandler):
    op_code = t.NAWS
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


class MSPHandler(TelnetOptionHandler):
    """
    Mud Sound Protocol - http://www.zuggsoft.com/zmud/msp.htm
    Not to be confused with MSSP above.
    """
    op_code = bytes([90])
    op_name = "MSP"

    will = True

    def play_sound(self):
        pass

    def stop_sound(self):
        pass

    def play_music(self):
        pass

    def stop_music(self):
        pass


class MudTelnetProtocol(t.Telnet):

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

    def enableRemote(self, option):
        if (handler := self.handler_codes.get(option, None)):
            handler.enableRemote()
            return True

    def enableLocal(self, option):
        if (handler := self.handler_codes.get(option, None)):
            handler.enableLocal()
            return True

    def disableLocal(self, option):
        # Pass this request along to our handlers, if available.
        if (handler := self.handler_codes.get(option, None)):
            handler.disableLocal()

    def disableRemote(self, option):
        # Pass this message along to our handlers, if available.
        if (handler := self.handler_codes.get(option, None)):
            handler.disableRemote()

    # Re-implements the normal _write to allow for MCCP2 outgoing.
    def _write_plain(self, data):
        self.transport.write(data)

    def _write_mccp2(self, data):
        self.transport.write(self.mccp2.compress(data) + self.mccp2.flush(zlib.Z_SYNC_FLUSH))

    def _dataReceived_plain(self, data):
        super().dataReceived(data)

    def _dataReceived_mccp3(self, data):
        pass

    def __init__(self):
        super().__init__()
        # Clone a protocol flags dict from the class property.
        self.protocol_flags = dict(self.default_protocol_flags)
        # When MCCP2 is enabled/disabled, self._write is swapped between the two versions.
        self._write = self._write_plain
        # When MCCP3 is enabled/disabled, self.dataReceived is swapped between the two versions.
        self.dataReceived = self._dataReceived_plain
        self.data_buffer = []
        self.command_list = []
        self.app_state = 'newline'
        self.handler_codes = dict()
        self.handler_names = dict()
        for h_class in self.handler_classes:
            handler = h_class(self)
            self.handler_codes[h_class.op_code] = handler
            self.handler_names[h_class.op_name] = handler

    def applicationDataReceived(self, data):
        """
        This is called by super().dataReceived() and it receives a pile of bytes.
        This will never contain IAC-escaped sequences, but may contain other special
        characters/symbols/bytes.
        """
        # First, append all the new data to our app buffer.

        for b in iterbytes(data):

            if b == t.NULL:
                # Ignoring this ancient keepalive
                # convert it to the IDLE COMMAND here...
                self.command_list.append("IDLE")
                continue
            if b == t.LF:
                self.command_list.append(b''.join(self.data_buffer))
                self.data_buffer.clear()
                continue

            # Nothing else stands out? Append the data to data buffer...
            self.data_buffer.append(b)

        # We have pending commands. What're we gonna do with them?
        for command in self.command_list:
            self.decodeCommand(command)
        self.command_list.clear()

    def decodeCommand(self, command):
        """
        Decodes user-entered command into preferred style, such as UTF-8.

        Args:
            command (byte string): The user-entered command, minus terminating CRLF
        """
        decoded = command.decode("utf-8", errors='ignore')
        print(f"SUCCESSFULLY DECODED COMMAND: {decoded}")
        self._write(f"TELNET ECHO: {decoded}\r\n")

    def connectionMade(self):

        for handler in self.handler_codes.values():
            if handler.will:
                handler.start()
