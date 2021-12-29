

import time
from component import Component
from packet_manager import PacketManager
from radio import Radio


class Node():
    radio: Radio = None
    components: dict[str, Component] = None
    packet_manager: PacketManager = None

    def __init__(self, radio: Radio, components: dict[str, Component], packet_manager: PacketManager):
        self.radio = radio
        self.components = components
        self.packet_manager = packet_manager

    def process(self):
        self.radio.run_periodic()
        self.packet_manager.run_periodic()

        for (_, component) in self.components.items():
            component.run_periodic()
        time.sleep(.25)
