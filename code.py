import json

from node import Node
from packet_manager import PacketManager, get_packet_manager


def init_component(config):
    if config["type"] == "LED":
        from led import Led
        return Led(config["params"])
    elif config["type"] == "LED Strip":
        from led_strip import LedStrip
        return LedStrip(config["params"])
    elif config["type"] == "LED Commander":
        from led_commander import LedCommander
        return LedCommander(config["params"])
    elif config["type"] == "Serial Linux":
        from serial_linux import SerialLinux
        return SerialLinux(config["params"])
    elif config["type"] == "Serial Pico":
        from serial_pico import SerialPico
        return SerialPico(config["params"])

with open("config.json") as f:
    config = json.load(f)

node_id = config["id"]

print("Running as", config["name"])

components_config = config["components"]

radio_config = None
if "radio" in components_config:
    radio_config = components_config["radio"]
    del components_config["radio"]

components = {}
for (name, component_config) in components_config.items():
    components[name] = init_component(component_config)

subscriptions = []
for (_, component) in components.items():
    subscriptions.append({"component": component, "component_subscriptions": component.get_subscriptions()})

if "peripherals" in config:
    from peripheral_manager import get_peripheral_manager

    peripherals_config = config["peripherals"]
    for (name, peripheral_config) in peripherals_config.items():
        get_peripheral_manager().initialize_peripheral(name, peripheral_config)

packet_manager = get_packet_manager(subscriptions, node_id)

radio = None
if not radio_config is None:
    from radio import Radio
    radio = Radio(packet_manager, radio_config["params"])

node = Node(radio, components, packet_manager)

while True:
    node.process()
