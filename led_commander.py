
import time
from component import Component
from packet import Packet
from packet_manager import get_packet_manager

TYPE_LED = 0x01

class LedCommander(Component):
    def __init__(self, params: dict):
        self.value = True
        self.device_id = params["device_id"]
        self.blink = True
        self.blink_on =  params["on"]
        self.blink_off = params["off"]
        self.blink_last_change = time.monotonic_ns()

    def run_periodic(self):
        if self.blink:
            if self.value: # LED is on
                if time.monotonic_ns() - self.blink_last_change > self.blink_on:
                    get_packet_manager().queue_outgoing_packet(Packet(1, 0, 0, 0, 0, TYPE_LED, self.device_id, b'\x2A\x00'))
                    self.value = False
                    self.blink_last_change = time.monotonic_ns()
            elif not self.value: # LED is off
                if time.monotonic_ns() - self.blink_last_change > self.blink_off:
                    get_packet_manager().queue_outgoing_packet(Packet(1, 0, 0, 0, 0, TYPE_LED, self.device_id, b'\x2A\x01'))
                    self.value = True
                    self.blink_last_change = time.monotonic_ns()

    def get_subscriptions(self):
        return []