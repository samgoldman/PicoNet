import struct
from component import Component
from packet import Packet
from pin_map import get_pin
import pwmio
import time

TYPE_LED_STRIP = 0x02
TYPE_LED_STRIP_COMMANDER = 0x03
### COMMMANDS ###
NOOP      = 0x00
SET_RED   = 0x01
SET_GREEN = 0x02
SET_BLUE  = 0x03
SET_ALL   = 0x04
#################

def clamp_value(value):
    return min(0xffff, max(0, value))

class LedStrip(Component):
    red_pwm: pwmio.PWMOut
    green_pwm: pwmio.PWMOut
    blue_pwm: pwmio.PWMOut

    def __init__(self, params: dict):
        self.red_pwm = pwmio.PWMOut(get_pin(params["red_pin"]), frequency=1000)
        self.green_pwm = pwmio.PWMOut(get_pin(params["green_pin"]), frequency=1000)
        self.blue_pwm = pwmio.PWMOut(get_pin(params["blue_pin"]), frequency=1000)
        
        self.device_type = TYPE_LED_STRIP
        self.device_id = params["device_id"]
    
    def set_red_percent(self, value):
        self.red_pwm.duty_cycle = clamp_value(value)

    def set_green_percent(self, value):
        self.green_pwm.duty_cycle = clamp_value(value)

    def set_blue_percent(self, value):
        self.blue_pwm.duty_cycle = clamp_value(value)

    def run_periodic(self):
        pass

    def process_packet(self, packet: Packet):
        command = packet.payload[0]
        if command == NOOP:
            pass
        elif command == SET_RED or command == SET_GREEN or command == SET_BLUE or command == SET_ALL:
            (_, value, _) = struct.unpack('<BH47s', packet.payload)
            if command == SET_RED or command == SET_ALL:
                self.set_red_percent(value)
            if command == SET_GREEN or command == SET_ALL:
                self.set_green_percent(value)
            if command == SET_BLUE or command == SET_ALL:
                self.set_blue_percent(value)

    def get_subscriptions(self):
        return [{"device_type": self.device_type, "device_id": self.device_id}]


class LedStripCommander(Component):
    def __init__(self, params: dict):
        self.value = True
        self.device_id = params["device_id"]
        self.red_value = -1
        self.green_value = -1
        self.blue_value = -1
        self.destination = params["destination"]
        # self.

    def run_periodic(self):
        pass
        # if self.blink:
        #     if self.value: # LED is on
        #         if time.monotonic_ns() - self.blink_last_change > self.blink_on:
        #             get_packet_manager().queue_outgoing_packet(Packet(1, 0, 0, 0, 0, TYPE_LED_STRIP, self.device_id, b'\x2A\x00'))
        #             self.value = False
        #             self.blink_last_change = time.monotonic_ns()
        #     elif not self.value: # LED is off
        #         if time.monotonic_ns() - self.blink_last_change > self.blink_off:
        #             get_packet_manager().queue_outgoing_packet(Packet(1, 0, 0, 0, 0, TYPE_LED_STRIP, self.device_id, b'\x2A\x01'))
        #             self.value = True
        #             self.blink_last_change = time.monotonic_ns()


    def process_packet(self, packet: Packet):
        pass

    def get_subscriptions(self):
        return []
