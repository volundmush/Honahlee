from honahlee.networking.base import GameClientProtocol
import telnetlib as tl

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


class TelnetOptionHandler:
    op_code = None

    def __init__(self, protocol):
        self.protocol = protocol


class MXPHandler(TelnetOptionHandler):
    op_code = MXP


class MCCP2Handler(TelnetOptionHandler):
    op_code = MCCP2


class MCCP3Handler(TelnetOptionHandler):
    op_code = MCCP3


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
        MXP: MXPHandler,
        MCCP2: MCCP2Handler,
        MCCP3: MCCP3Handler,
    }

    def __init__(self):
        super().__init__()
        self.state = 0
        self.handlers = {key: value(self) for key, value in self.handler_classes.items()}
        self.command_buffer = bytearray()
        self.command_mode = 0
        self.sb_buffer = bytearray()
        self.sb_command = 0

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
            if command == tl.WILL:
                self.send_bytes(bytes([tl.DONT, op_code]))
            if command == tl.DO:
                self.send_bytes(bytes([tl.WONT, op_code]))
            # No reason to respond to a random IAC WONT that wasn't preceded with a WILL/DO...

    def execute_line(self, buffer):
        pass

    def execute_sb(self, op_code, data):
        handler = self.handlers.get(op_code, None)
        if handler:
            # We support this feature. pass the data up to the handler.
            handler.receive_sb(data)
        else:
            # We do not support this feature. let's complain I guess? Gotta check specs.
            pass

    def send_bytes(self, data):
        # need to stick MCCP3 handling in here shortly. if mccp3, compress outgoing
        self.final_send_bytes(data)

    def data_received(self, data):
        # Gotta stick MCCP2 handling in here shortly. if mccp2, decompress incoming.
        self.process_bytes(data)

    def process_bytes(self, data):
        for b in data:

            # for DATA STATE
            if self.state == TSTATE.DATA:
                if b == tl.IAC:
                    # Receiving an IAC puts us in ESCAPED state.
                    self.state = TSTATE.ESCAPED
                    continue
                if b == b'\r':
                    # Receiving an \r puts us in endline state.
                    self.state = TSTATE.ENDLINE
                    continue
                # Anything else is just data.
                self.command_buffer.append(b)
                continue

            # for ESCAPED state, which begins with an IAC.
            if self.state == TSTATE.ESCAPED:
                if b in (tl.WILL, tl.WONT, tl.DO, tl.DONT):
                    # Receiving WILl, WONT, DO, or DONT puts us in command mode where we await an option code.
                    self.state = TSTATE.COMMAND
                    self.command_mode = b
                    continue
                if b == tl.SB:
                    # Receiving SB after IAC puts us in SUBNEGOTIATION mode.
                    self.state = TSTATE.SUBNEGOTIATION
                    self.sb_command = 0
                    continue
                if b == tl.IAC:
                    # An IAC after an IAC is just an escape for byte 255. Append to command buffer and move on.
                    self.state = TSTATE.DATA
                    self.command_buffer.append(tl.IAC)
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
                if b == tl.IAC:
                    self.state = TSTATE.SUB_ESCAPED
                    continue
                self.sb_buffer.append(b)
                continue

            if self.state == TSTATE.SUB_ESCAPED:
                if b == tl.SE:
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
                if b in (b'\n', tl.IAC):
                    # The most common situation is that players are entering commands which terminate with CRLF (\r\n)
                    self.execute_line(self.command_buffer)
                    self.command_buffer.clear()
                    self.state = TSTATE.DATA
                    continue
                # but otherwise, just keep appending to command buffer.
                self.command_buffer.append(b)
                self.state = TSTATE.DATA
                continue
