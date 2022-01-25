import usb_cdc
import adafruit_logging

from packet import Packet
from component import Component
from packet_manager import get_packet_manager

class SerialPico(Component):
    ser: usb_cdc.Serial
    known_nodes: list

    def __init__(self, params: dict):
        self.node = params["node"]
        self.known_nodes = params["known_nodes"]

        self.ser = usb_cdc.data
        self.ser.timeout = 0
       
        _ = self.ser.read(2048)
        assert(self.ser.in_waiting == 0)
        self.logger = adafruit_logging.getLogger('logger')

    def send(self, packet: Packet):
        raw = packet.pack()
        bytes_written = self.ser.write(raw)
        self.logger.debug('Serial Pico: wrote %d bytes', bytes_written)
        self.ser.flush()
        self.logger.debug('Serial Pico: flushed')

    def run_periodic(self):
        if self.ser.in_waiting >= 60:
            raw_bytes = self.ser.read(60)
            assert(len(raw_bytes) == 60)

            get_packet_manager().queue_received_packet(Packet.unpack(raw_bytes))

        outgoing_packet = get_packet_manager().pop_outgoing_packet(self.known_nodes)
        if not outgoing_packet is None:
            self.send(outgoing_packet)

    def process_packet(self):
        # Will eventually have commands, but not yet
        raise NotImplementedError()

    def get_subscriptions(self):
        return []
