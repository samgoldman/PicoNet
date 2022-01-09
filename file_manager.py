from component import Component
from packet import Packet
from microcontroller import watchdog

TYPE_FILE_MANAGER = 0x04

COMMAND_NOOP   = 0x00
# Upload commands
COMMAND_RESET  = 0x01
COMMAND_APPEND = 0x02
COMMAND_SAVE   = 0x03
# File manipulation commands
COMMAND_REMOVE = 0x04
COMMAND_RENAME = 0x05

RESPONSE_OK       = 0x01
RESPONSE_READONLY = 0x02

class WatchdogManager(Component):
    def __init__(self, params: dict):
        self.timeout = params["timeout"]
        

        self.initialized = False

        if params["construct_initialized"]:
            self.initialize()

        self.feed_count = 0

    def run_periodic(self):
        if not self.initialized:
            self.initialize()

        watchdog.feed()
        self.feed_count += 1

    def process_packet(self, packet: Packet):
        pass # No commands defined right now

    def get_subscriptions(self):
        pass # No commands right now
