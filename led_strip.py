import struct
from component import Component
from packet import Packet
from pin_map import get_pin
import pwmio
import time

TYPE_LED_STRIP = 0x02
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
