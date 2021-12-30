import digitalio
import time

from microcontroller import Pin
from component import Component
from packet import Packet
from pin_map import get_pin

TYPE_LED = 0x01

class Led(Component):
    def __init__(self, params: dict):
        self.led = digitalio.DigitalInOut(get_pin(params["pin"]))
        self.led.direction = digitalio.Direction.OUTPUT
        self.led.value = False

        if not params is None and "value" in params:
            self.led.value = params["value"]
        
        self.device_type = TYPE_LED
        self.device_id = params["device_id"]
        self.blink = False
        self.blink_on = 0
        self.blink_off = 0
        self.blink_last_change = time.monotonic_ns()

    def run_periodic(self):
        if self.blink:
            if self.led.value: # LED is on
                if time.monotonic_ns() - self.blink_last_change > self.blink_on:
                    self.led.value = False
                    self.blink_last_change = time.monotonic_ns()
            elif not self.led.value: # LED is off
                if time.monotonic_ns() - self.blink_last_change > self.blink_off:
                    self.led.value = True
                    self.blink_last_change = time.monotonic_ns()

    def process_packet(self, packet: Packet):
        if packet.payload[0] == 0x2A:
            if packet.payload[1] == 0:
                self.led.value = False
                print("LED off")
            elif packet.payload[1] == 1:
                self.led.value = True
                print("LED on")

    def get_subscriptions(self):
        return [{"device_type": self.device_type, "device_id": self.device_id}]



