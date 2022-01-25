

import time
import adafruit_logging
from component import Component
from packet_manager import PacketManager


class Node():
    components = None
    packet_manager: PacketManager = None

    def __init__(self, components, packet_manager: PacketManager):
        self.components = components
        self.packet_manager = packet_manager
        self.logger = adafruit_logging.getLogger('logger')

    def process(self):
        try:
            self.packet_manager.run_periodic()
        except Exception as e:
            self.logger.error(f"Packet manager threw an exception: {e}")

        for (name, component) in self.components.items():
            try:
                component.run_periodic()
            except Exception as e:
                self.logger.error(f"Component '{name}' threw an exception: {e}")
