import time
import traceback
from packet import Packet
from component import Component
import os
import adafruit_logging as logging

TYPE_PACKET_MANAGER = 0x05

PACKET_TYPE_DATA = 0x1
PACKET_TYPE_ACK     = 0x2
PACKET_TYPE_ACK_REQUESTED = 0x80

TIMEOUT = 1000 #ns

class PacketManager():
    logger: logging.Logger

    def __init__(self):
        self.subscriptions = []
        self.node = None
        self.received_packets = []
        self.outgoing_packets = []
        self.sent_packets = []
        self.logger = logging.getLogger('logger')

    def queue_received_packet(self, packet: Packet):
        self.logger.debug("Received packet with ID %8x", packet.packet_id)

        if packet.destination != self.node:
            self.outgoing_packets.append(packet)
            self.logger.info("Forwarding packet %8x from node %d to node %d (is_ack=%s)", packet.packet_id, packet.origin, packet.destination, packet.packet_type == PACKET_TYPE_ACK)
        else:
            self.received_packets.append(packet)
            if packet.packet_type & PACKET_TYPE_ACK_REQUESTED > 0:
                self.logger.info("Queueing ACK for packet %8x", packet.packet_id)
                ack_packet = Packet(PACKET_TYPE_ACK, packet.packet_id, packet.origin, 0, 0, 0, b'\x00'*Packet.get_max_payload_size())
                self.queue_outgoing_packet(ack_packet)

    def queue_outgoing_packet(self, packet: Packet):
        if packet.destination == -1: # Internal messages
            self.received_packets.append(packet)
        else:
            if packet.packet_id is None:
                packet.packet_id = int.from_bytes(os.urandom(4), 'big')
            
            if packet.origin == -1:
                packet.origin = self.node

            self.logger.debug("Queueing outgoing packet 0x%8x to node %d", packet.packet_id, packet.destination)
            self.outgoing_packets.append(packet)

    def pop_outgoing_packet(self, known_nodes) -> Packet:
        for i in range(len(self.outgoing_packets)):
            if self.outgoing_packets[i].destination in known_nodes:
                packet = self.outgoing_packets.pop(i)
                if packet.origin == self.node and packet.packet_type & PACKET_TYPE_ACK_REQUESTED > 0:
                    self.sent_packets.append((packet, time.monotonic_ns()))
                return packet

        return None

    def run_periodic(self):
        if len(self.received_packets) != 0:
            packet: Packet = self.received_packets.pop(0) # FIFO
            if packet.packet_type == PACKET_TYPE_ACK:
                for i in range(len(self.sent_packets)):
                    if self.sent_packets[i][0].packet_id == packet.packet_id:
                        self.logger.debug("Received ACK for packet %8x, popping", packet.packet_id)
                        self.sent_packets.pop(i)
                        break
            else:
                for sub in self.subscriptions:
                    comp: Component = sub["component"]
                    comp_subs = sub["component_subscriptions"]
                    if comp_subs is None:
                        continue

                    for sub in comp_subs:
                        if sub["device_type"] == packet.payload_type and sub["device_id"] == packet.payload_device_id:
                            try:
                                comp.process_packet(packet)
                            except Exception as e:
                                self.logger.error("Packet Manager: component '%s' threw an exception ('%s'): \n%s", comp, e, ''.join(traceback.format_exception(None, e, e.__traceback__)))
                            return

        for i in range(len(self.sent_packets)):
            entry = self.sent_packets[i]
            packet: Packet = entry[0]
            timestamp: int = entry[1]
            elapsed = time.monotonic_ns() - timestamp
            if elapsed > 100000000:
                self.sent_packets.pop(i)
                self.logger.info(f"Packet Manager: resending packet 0x{packet.packet_id:08x}")
                self.queue_outgoing_packet(packet)
                break

_packet_manager_instance: PacketManager = None

def get_packet_manager() -> PacketManager:
    global _packet_manager_instance
    if _packet_manager_instance is None:
        _packet_manager_instance = PacketManager()
    return _packet_manager_instance