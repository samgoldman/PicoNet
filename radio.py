from adafruit_rfm69 import RFM69
import digitalio

from packet import Packet
from component import Component
from packet_manager import get_packet_manager
from peripheral_manager import get_peripheral_manager
from pin_map import get_pin


RADIO_FREQ_MHZ = 915.0

class Radio(Component):
    radio: RFM69
    known_nodes: list

    def __init__(self, params: dict):
        radio_cs = digitalio.DigitalInOut(get_pin(params["cs"]))
        radio_cs.direction = digitalio.Direction.OUTPUT

        radio_reset = digitalio.DigitalInOut(get_pin(params["reset"]))
        radio_reset.direction = digitalio.Direction.OUTPUT

        self.node = params["node"]
        self.known_nodes = params["known_nodes"]

        self.packet_manager = get_packet_manager()
        self.radio = RFM69(get_peripheral_manager().get_peripheral(params["spi"]), radio_cs, radio_reset, RADIO_FREQ_MHZ)
        self.radio.node = self.node

    def send(self, packet: Packet):
        raw = packet.pack()
        self.radio.send(raw, destination=packet.destination)

    def run_periodic(self):
        packet = self.radio.receive(timeout=0)

        if not packet is None:
            self.packet_manager.queue_received_packet(Packet.unpack(packet))

        outgoing_packet = self.packet_manager.pop_outgoing_packet(self.known_nodes)
        if not outgoing_packet is None:
            self.send(outgoing_packet)

    def process_packet(self):
        # Will eventually have commands, but not yet
        raise NotImplementedError()

    def get_subscriptions(self):
        return []
