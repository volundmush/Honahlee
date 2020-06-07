from honahlee.networking.base import GameClientProtocol
import zlib

class TCODES:
    NUL = 0
    BEL = 7
    CR = 13
    LF = 10
    SGA = 3
    NAWS = 31
    SE = 240
    NOP = 241
    GA = 249
    SB = 250
    WILL = 251
    WONT = 252
    DO = 253
    DONT = 254
    IAC = 255

    # Adding more codes to the Telnet codes available.
    # MUD eXtension Protocol
    MXP = 91

    # Mud Server Status Protocol
    MSSP = 70

    # Mud Client Compression Protocol
    MCCP2 = 86
    MCCP3 = 87

    # Generic Mud Communication Protocol
    GMCP = 201

    # Mud Server Data Protocol
    MSDP = 69


class TelnetOptionHandler:
    op_code = None
    order = 0

    def __init__(self, protocol):
        self.protocol = protocol
        self.enabled = False
        self.received = 0
        self.sent = 0

    def enable(self):
        print(f"ENABLING {self}")
        pass

    def disable(self):
        print(f"DISABLING {self}")
        pass

    def will(self):
        self.sent = TCODES.WILL
        self.protocol.send_bytes(bytes([TCODES.IAC, TCODES.WILL, self.op_code]))

    def receive_command(self, command):
        print(f"{self} RECEIVED COMMAND: {command}")
        if self.enabled:
            if command in (TCODES.DONT, TCODES.WONT):
                self.disable()
                self.enabled = False
            # ignore DO or WILL if already enabled.
        else:
            if (command == TCODES.DO and self.sent == TCODES.WILL) or (command == TCODES.WILL and self.sent == TCODES.DO):
                # We have received a positive response from client. Enable this option.
                self.enable()
                self.enabled = True
                self.sent = 0
            if (command == TCODES.DONT and self.sent == TCODES.WILL) or (command == TCODES.WONT and self.sent == TCODES.DO):
                # the command has rejected our negotiation. Do not enable this option.
                pass

    def receive_sb(self, data):
        pass

    def send_sb(self, data):
        self.protocol.send_bytes(bytes([TCODES.IAC, TCODES.SB, self.op_code, *data, TCODES.IAC, TCODES.SE]))


class MXPHandler(TelnetOptionHandler):
    op_code = TCODES.MXP


class MCCP2Handler(TelnetOptionHandler):
    op_code = TCODES.MCCP2

    def enable(self):
        self.send_sb([])
        self.protocol.mccp2 = zlib.compressobj(9)


class MCCP3Handler(TelnetOptionHandler):
    op_code = TCODES.MCCP3


# Yeah this is basically an enum.
class TSTATE:
    DATA = 0
    ESCAPED = 1
    SUBNEGOTIATION = 2
    IN_SUBNEGOTIATION = 3
    SUB_ESCAPED = 4
    COMMAND = 5
    ENDLINE = 6


class TelnetProtocol(GameClientProtocol):
    handler_classes = {
        TCODES.MXP: MXPHandler,
        TCODES.MCCP2: MCCP2Handler,
        TCODES.MCCP3: MCCP3Handler,
    }

    def __init__(self):
        super().__init__()
        self.state = 0
        self.handlers = {key: value(self) for key, value in self.handler_classes.items()}
        self.command_buffer = bytearray()
        self.command_mode = 0
        self.sb_buffer = bytearray()
        self.sb_command = 0
        self.mccp2 = None
        self.mccp3 = None

    def on_connection_made(self, transport):
        for op_code, handler in sorted(self.handlers.items(), key=lambda x: x[1].order):
            handler.will()


    @classmethod
    def register_handler(cls, op_code, handler_class):
        """
        Used to add new Option Handlers to the TelnetProtocol class. Called by mods/plugins.
        """
        cls.handler_classes[op_code] = handler_class

    def execute_iac_command(self, command, op_code):
        handler = self.handlers.get(op_code, None)
        if handler:
            # Support this feature. Pass the command received up to its handler.
            handler.receive_command(command)
        else:
            # We do NOT support this feature.
            if command == TCODES.WILL:
                self.send_bytes(bytes([TCODES.DONT, op_code]))
            if command == TCODES.DO:
                self.send_bytes(bytes([TCODES.WONT, op_code]))
            # No reason to respond to a random IAC WONT that wasn't preceded with a WILL/DO...

    def execute_line(self, buffer):
        self.client.execute_command(buffer)

    def execute_sb(self, op_code, data):
        handler = self.handlers.get(op_code, None)
        if handler:
            # We support this feature. pass the data up to the handler.
            handler.receive_sb(data)
        else:
            # We do not support this feature. let's complain I guess? Gotta check specs.
            pass

    def send_bytes(self, data):
        # if mccp2, compress outgoing
        if self.mccp2:
            data = self.mccp2.compress(data) + self.mccp2.flush(zlib.Z_SYNC_FLUSH)
        self.final_send_bytes(data)

    def data_received(self, data):
        # Gotta stick MCCP3 handling in here shorTCODES.. if mccp3, decompress incoming.
        self.process_bytes(data)

    def process_bytes(self, data):
        print(f"RECEIVED BYTES: {type(data)} {data}")
        for b in data:
            print(f"PROCESSING {type(b)} {b}")
            print(f"{self} CURRENT MODE: {self.state}")
            # for DATA STATE
            if self.state == TSTATE.DATA:
                print(f"{self} IS IN DATA MODE RECEIVED {b}")
                if b == TCODES.IAC:
                    print(f"{self} ENTERING ESCAPE MODE")
                    # Receiving an IAC puts us in ESCAPED state.
                    self.state = TSTATE.ESCAPED
                    continue
                if b == TCODES.CR:
                    # Receiving an \r puts us in endline state.
                    self.state = TSTATE.ENDLINE
                    continue
                # Anything else is just data.
                self.command_buffer.append(b)
                continue

            # for ESCAPED state, which begins with an IAC.
            if self.state == TSTATE.ESCAPED:
                if b in (TCODES.WILL, TCODES.WONT, TCODES.DO, TCODES.DONT):
                    # Receiving WILl, WONT, DO, or DONT puts us in command mode where we await an option code.
                    self.state = TSTATE.COMMAND
                    self.command_mode = b
                    continue
                if b == TCODES.SB:
                    # Receiving SB after IAC puts us in SUBNEGOTIATION mode.
                    self.state = TSTATE.SUBNEGOTIATION
                    self.sb_command = 0
                    continue
                if b == TCODES.IAC:
                    # An IAC after an IAC is just an escape for byte 255. Append to command buffer and move on.
                    self.state = TSTATE.DATA
                    self.command_buffer.append(TCODES.IAC)
                    continue

            if self.state == TSTATE.COMMAND:
                # After receiving an IAC WILL, WONT, DO, or DONT, we must call execute_iac_command with the new byte.
                # This is something like 'IAC WILL MCCP2'
                self.execute_iac_command(self.command_mode, b)
                self.command_mode = 0
                self.state = TSTATE.DATA
                continue

            if self.state == TSTATE.SUBNEGOTIATION:
                # The byte immediately following an IAC SB is an op_code.
                self.state = TSTATE.IN_SUBNEGOTIATION
                self.sb_command = b
                self.sb_buffer.clear()
                continue

            if self.state == TSTATE.IN_SUBNEGOTIATION:
                # After receiving IAC SB <code>, we begin appending to the sb_buffer until we get an IAC SE.
                if b == TCODES.IAC:
                    self.state = TSTATE.SUB_ESCAPED
                    continue
                self.sb_buffer.append(b)
                continue

            if self.state == TSTATE.SUB_ESCAPED:
                if b == TCODES.SE:
                    # End sub-negotiation!
                    self.execute_sb(self.sb_command, self.sb_buffer)
                    self.sb_command = 0
                    self.sb_buffer.clear()
                    self.state = TSTATE.DATA
                    continue
                # Anything besides an SE will just become part of the buffer... and we go back to IN_SUBNEGOTIATION mode
                self.sb_buffer.append(b)
                self.state = TSTATE.IN_SUBNEGOTIATION
                continue

            if self.state == TSTATE.ENDLINE:
                if b in (TCODES.LF, TCODES.IAC):
                    # The most common situation is that players are entering commands which terminate with CRLF (\r\n)
                    self.execute_line(self.command_buffer)
                    self.command_buffer.clear()
                    self.state = TSTATE.DATA
                    continue
                # but otherwise, just keep appending to command buffer.
                self.command_buffer.append(b)
                self.state = TSTATE.DATA
                continue
