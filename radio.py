import adafruit_logging
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

        self.logger = adafruit_logging.getLogger('logger')

        self.packet_manager = get_packet_manager()
        self.radio = RFM69(get_peripheral_manager().get_peripheral(params["spi"]), radio_cs, radio_reset, RADIO_FREQ_MHZ)
        self.radio.node = self.node

        self.logger.info('Radio: initialized with known nodes: %s', self.known_nodes)
        self.logger.info('Radio: I am node %d (%d)', self.radio.node, self.radio.node)
        self.logger.debug('Radio: frequency %s', self.radio.frequency_mhz)
        self.logger.debug('Radio: bitrate %s', self.radio.bitrate)
        self.logger.debug('Radio: frequency deviation %s', self.radio.frequency_deviation)
        self.logger.debug('Radio: temperature %s', self.radio.temperature)
        self.logger.debug('Radio: sync_word 0x%08x', int.from_bytes(self.radio.sync_word, 'little'))


    def send(self, packet: Packet):
        self.logger.debug("Radio: sending packet with id 0x%08x to node %d", packet.packet_id, packet.destination)
        raw = packet.pack()

        success = self.radio.send(raw)
        if not success:
            self.logger.error("Radio: failed to send packet with id 0x%08x", packet.packet_id)
        else:
            self.logger.debug("Radio: sent packet with id 0x%04x", packet.packet_id)

    def run_periodic(self):
        packet = self.radio.receive(timeout=.5)

        if not packet is None:
            self.logger.debug("Radio: attempting to unpack packet")
            unpacked = Packet.unpack(packet)
            self.logger.debug("Radio: received a packet with id 0x%08x", unpacked.packet_id)
            self.packet_manager.queue_received_packet(unpacked)
            self.logger.debug("Radio: RSSI=%f", self.radio.rssi)

        outgoing_packet = self.packet_manager.pop_outgoing_packet(self.known_nodes)
        if not outgoing_packet is None:
            self.send(outgoing_packet)

    def process_packet(self):
        # Will eventually have commands, but not yet
        raise NotImplementedError()

    def get_subscriptions(self):
        return []
