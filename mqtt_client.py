



from component import Component
from packet import Packet
import serial
import struct
import json
import paho.mqtt.client as mqtt

TYPE_MQTT_CLIENT = 0x03


TYPE_LED_STRIP = 0x02
### COMMMANDS ###
NOOP      = 0x00
SET_RED   = 0x01
SET_GREEN = 0x02
SET_BLUE  = 0x03
SET_ALL   = 0x04
#################

def generate_led_strip_command(node, device_id, command, value):
    PACKING_FORMAT = "<BBBBIBBBH47s"
    data = struct.pack(PACKING_FORMAT, 0, 
                                       0, 
                                       0, 
                                       node, 
                                       0, 
                                       TYPE_LED_STRIP, 
                                       device_id,
                                       command,
                                       value,
                                       b'\x00'*47)
    assert(len(data) == 60)
    return data

class MqttClient(Component):
    def __init__(self, params: dict):
        self.serial_device = params["serial_device"]
        self.ser = serial.Serial(self.serial_device)

        self.client = mqtt.Client(client_id="linux_led_strip_client_0")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(params["server_ip"], params["server_port"], params["timeout"])
        self.on_connect(None, None, 0)

    def on_connect(self, userdata, flags, rc):
        print("Connected with result code", rc)

        self.client.subscribe("/led_strips/#")
        self.client.subscribe("/led_strips_commander/#")

    def on_message(self, client, userdata, msg):
        if msg.topic == "/led_strips/cmd":
            cmd = json.loads(msg.payload.decode("utf-8"))
            pico_cmd = generate_led_strip_command(cmd["node"], 1, cmd["cmd"], cmd["value"])
            self.ser.write(pico_cmd)
        if msg.topic == "/led_strips_commander/shutdown":
            self.ser.close()
            exit()

    def run_periodic(self):
        self.client.loop()

    def process_packet(self, packet: Packet):
        pass # No commands defined right now

    def get_subscriptions(self):
        pass # No commands right now
