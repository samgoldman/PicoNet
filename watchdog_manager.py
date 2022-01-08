from component import Component
from packet import Packet
from pin_map import get_pin
from microcontroller import watchdog
from watchdog import WatchDogMode

TYPE_WATCHDOG = 0x03

class WatchdogManager(Component):
    def __init__(self, params: dict):
        self.timeout = params["timeout"]
        

        self.initialized = False

        if params["construct_initialized"]:
            self.initialize()

        self.feed_count = 0

    def initialize(self):
            watchdog.timeout = self.timeout
            watchdog.mode = WatchDogMode.RESET
            self.initialized = True


    def run_periodic(self):
        if not self.initialized:
            self.initialize()

        watchdog.feed()
        self.feed_count += 1

    def process_packet(self, packet: Packet):
        pass # No commands defined right now

    def get_subscriptions(self):
        pass # No commands right now
