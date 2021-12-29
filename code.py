import json

from node import Node
from led import Led, LedCommander
from led_strip import LedStrip
from packet_manager import PacketManager, get_packet_manager
from peripheral_manager import get_peripheral_manager
from radio import Radio


def init_component(config) -> function:
    if config["type"] == "LED":
        return Led(config["params"])
    elif config["type"] == "LED Strip":
        return LedStrip(config["params"])
    elif config["type"] == "LED Commander":
        return LedCommander(config["params"])

with open("config.json") as f:
    config = json.load(f)

node_id = config["id"]

components_config = config["components"]
peripherals_config = config["peripherals"]

radio_config = components_config["radio"]
del components_config["radio"]

components = {}
for (name, component_config) in components_config.items():
    components[name] = init_component(component_config)

subscriptions = []
for (_, component) in components.items():
    subscriptions.append({"component": component, "component_subscriptions": component.get_subscriptions()})

for (name, peripheral_config) in peripherals_config.items():
    get_peripheral_manager().initialize_peripheral(name, peripheral_config)

packet_manager = get_packet_manager(subscriptions)
radio = Radio(packet_manager, radio_config["params"])

node = Node(radio, components, packet_manager)

while True:
    node.process()
