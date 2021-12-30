

import time
from component import Component
from packet_manager import PacketManager


class Node():
    radio = None
    components = None
    packet_manager: PacketManager = None

    def __init__(self, radio, components, packet_manager: PacketManager):
        self.radio = radio
        self.components = components
        self.packet_manager = packet_manager

    def process(self):
        if self.radio:
            self.radio.run_periodic()
        self.packet_manager.run_periodic()

        for (_, component) in self.components.items():
            component.run_periodic()
        time.sleep(.25)
