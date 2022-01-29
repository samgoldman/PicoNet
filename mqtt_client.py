import adafruit_logging
from component import Component
from file_manager import COMMAND_INITIATE_DOWNLOAD, COMMAND_REMOVE, TYPE_FILE_MANAGER
from packet import Packet
from packet_manager import PACKET_TYPE_ACK_REQUESTED, PACKET_TYPE_DATA, get_packet_manager
import struct
import json
import paho.mqtt.client as mqtt

from utils import str_to_log_val

TYPE_MQTT_CLIENT = 0x03


TYPE_LED_STRIP = 0x02
### COMMMANDS ###
NOOP      = 0x00
SET_RED   = 0x01
SET_GREEN = 0x02
SET_BLUE  = 0x03
SET_ALL   = 0x04
#################


class MqttClient(Component):

    def __init__(self, params: dict):

        self.client = mqtt.Client(client_id="linux_led_strip_client_0")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(params["server_ip"], params["server_port"], params["timeout"])
        self.on_connect(None, None, 0)

        self.client.loop_start()
        
        if "logger" in params:
            self.logger = adafruit_logging.getLogger(params["logger"]["name"])
            if "level" in params["logger"]:
                self.logger.setLevel(str_to_log_val(params["logger"]["level"]))
        else:
            self.logger = adafruit_logging.getLogger('logger')

    def on_connect(self, userdata, flags, rc):
        self.client.subscribe("/led_strips/#")
        self.client.subscribe("/led_strips_commander/#")
        self.client.subscribe("/linux_base_station/#")

    def generate_led_strip_command(self, node, device_id, command: int, value: int):
        PACKING_FORMAT = "<BH44s"
        try:
            packet = Packet(PACKET_TYPE_DATA | PACKET_TYPE_ACK_REQUESTED, None, node, 0, TYPE_LED_STRIP, device_id, struct.pack(PACKING_FORMAT, command, value, b'\x00'*44))
        except Exception as e:
            self.logger.error("MQTT Client: could not generate LED Strip packet: %s", str(e))
        return packet

    def on_message(self, client, userdata, msg):
        if msg.topic == "/led_strips/cmd":
            cmd = json.loads(msg.payload.decode("utf-8"))
            pico_cmd = self.generate_led_strip_command(cmd["node"], 1, cmd["cmd"], cmd["value"])
            if not pico_cmd is None:
                get_packet_manager().queue_outgoing_packet(pico_cmd)
        if msg.topic == "/led_strips_commander/shutdown":
            exit()
        if msg.topic == "/linux_base_station/initiate_download":
            cmd = json.loads(msg.payload.decode("utf-8"))

            payload = bytes([COMMAND_INITIATE_DOWNLOAD]) + b'\x00' + bytes([cmd["node"]]) + bytes(cmd["src"], 'utf-8') + b'\x00' + bytes(cmd["dst"], 'utf-8') + b'\x00'
            payload += (Packet.get_max_payload_size() - len(payload)) * b'\x00'
            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA | PACKET_TYPE_ACK_REQUESTED, None, -1, 0, TYPE_FILE_MANAGER, 0, payload))
        if msg.topic == "/linux_base_station/remove_file":
            cmd = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug("MQTT Client: received command %s", cmd)
            payload = bytes([COMMAND_REMOVE]) + bytes(cmd["src"], 'utf-8')
            payload += (Packet.get_max_payload_size() - len(payload)) * b'\x00'

            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA | PACKET_TYPE_ACK_REQUESTED, None, cmd["node"], 0, TYPE_FILE_MANAGER, 0, payload))


    def run_periodic(self):
        pass

    def process_packet(self, packet: Packet):
        pass # No commands defined right now

    def get_subscriptions(self):
        pass # No commands right now
