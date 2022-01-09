

import time
from component import Component
from packet_manager import PacketManager


class Node():
    components = None
    packet_manager: PacketManager = None

    def __init__(self, components, packet_manager: PacketManager):
        self.components = components
        self.packet_manager = packet_manager

    def process(self):
        try:
            self.packet_manager.run_periodic()
        except:
            pass # TODO: log/handle

        for (name, component) in self.components.items():
            try:
                start_time = time.monotonic_ns()
                component.run_periodic()
            except Exception as e:
                print(f"Component '{name}' threw an exception: {e}")
