from component import Component
from file_manager import COMMAND_INITIATE_DOWNLOAD, TYPE_FILE_MANAGER
from packet import Packet
from packet_manager import PACKET_TYPE_ACK_REQUESTED, PACKET_TYPE_DATA, get_packet_manager
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
    PACKING_FORMAT = "<BIBBIBBBH44s"
    packet = Packet(PACKET_TYPE_DATA | PACKET_TYPE_ACK_REQUESTED, None, 0, node, 0, TYPE_LED_STRIP, device_id, command, value, b'\x00'*44)
    return packet


class MqttClient(Component):

    def __init__(self, params: dict):

        self.client = mqtt.Client(client_id="linux_led_strip_client_0")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(params["server_ip"], params["server_port"], params["timeout"])
        self.on_connect(None, None, 0)

        self.client.loop_start()

    def on_connect(self, userdata, flags, rc):
        self.client.subscribe("/led_strips/#")
        self.client.subscribe("/led_strips_commander/#")
        self.client.subscribe("/linux_base_station/#")

    def on_message(self, client, userdata, msg):
        if msg.topic == "/led_strips/cmd":
            cmd = json.loads(msg.payload.decode("utf-8"))
            pico_cmd = generate_led_strip_command(cmd["node"], 1, cmd["cmd"], cmd["value"])
            get_packet_manager().queue_outgoing_packet(pico_cmd)
        if msg.topic == "/led_strips_commander/shutdown":
            exit()
        if msg.topic == "/linux_base_station/initiate_download":
            cmd = json.loads(msg.payload.decode("utf-8"))

            payload = bytes([COMMAND_INITIATE_DOWNLOAD]) + b'\x00' + bytes([cmd["node"]]) + bytes(cmd["src"], 'utf-8') + b'\x00' + bytes(cmd["dst"], 'utf-8') + b'\x00'
            payload += (Packet.get_max_payload_size() - len(payload)) * b'\x00'
            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA, None, 0, -1, 0, TYPE_FILE_MANAGER, 0, payload))


    def run_periodic(self):
        pass

    def process_packet(self, packet: Packet):
        pass # No commands defined right now

    def get_subscriptions(self):
        pass # No commands right now
