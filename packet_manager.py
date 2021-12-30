from packet import Packet
from component import Component
# from typing import List

class PacketManager():

    def __init__(self, subscriptions, node):
        self.subscriptions = subscriptions
        self.node = node
        self.received_packets = []
        self.outgoing_packets = []

    def queue_received_packet(self, packet: Packet):
        if packet.destination != self.node:
            self.outgoing_packets.append(packet)
            print("Forwarding packet...")
        else:
            self.received_packets.append(packet)

    def queue_outgoing_packet(self, packet: Packet):
        if packet.destination == -1: # Internal messages
            self.received_packets.append(packet)
        else:
            self.outgoing_packets.append(packet)

    def pop_outgoing_packet(self, known_nodes) -> Packet:
        for i in range(len(self.outgoing_packets)):
            if self.outgoing_packets[i].destination in known_nodes:
                packet = self.outgoing_packets.pop(i)
                return packet

        return None

    def run_periodic(self):
        if len(self.received_packets) != 0:
            packet = self.received_packets.pop()
            for sub in self.subscriptions:
                comp: Component = sub["component"]
                comp_subs = sub["component_subscriptions"]
                for sub in comp_subs:
                    if sub["device_type"] == packet.payload_type and sub["device_id"] == packet.payload_device_id:
                        comp.process_packet(packet)
                        return

_packet_manager_instance: PacketManager = None

def get_packet_manager(subscriptions=None, node=None) -> PacketManager:
    global _packet_manager_instance
    if _packet_manager_instance is None:
        _packet_manager_instance = PacketManager(subscriptions, node)
    return _packet_manager_instance