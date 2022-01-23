import json
from struct import pack
import adafruit_logging as logging
from node import Node
from packet_manager import get_packet_manager


def init_component(config):
    if config["type"] == "Radio":
        from radio import Radio
        return Radio(config["params"])
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
    elif config["type"] == "WatchdogManager":
        from watchdog_manager import WatchdogManager
        return WatchdogManager(config["params"])
    elif config["type"] == "MqttClient":
        from mqtt_client import MqttClient
        return MqttClient(config["params"])
    elif config["type"] == "FileManager":
        from file_manager import FileManager
        return FileManager(config["params"])

with open("config.json") as f:
    config = json.load(f)

# TODO: more in-depth logging system that allows different loggers for different instances
logger = logging.getLogger('logger')
level = config["log_level"]
if level == "NONE":
    logger.setLevel(logging.NOTSET)
if level == "DEBUG":
    logger.setLevel(logging.DEBUG)
if level == "INFO":
    logger.setLevel(logging.INFO)
if level == "WARNING":
    logger.setLevel(logging.WARNING)
if level == "ERROR":
    logger.setLevel(logging.ERROR)
if level == "CRITICAL":
    logger.setLevel(logging.CRITICAL)
logger.info("Log level: %s", level)

node_id = config["id"]

components_config = config["components"]

if "peripherals" in config:
    from peripheral_manager import get_peripheral_manager

    peripherals_config = config["peripherals"]
    for (name, peripheral_config) in peripherals_config.items():
        get_peripheral_manager().initialize_peripheral(name, peripheral_config)

components = {}
for (name, component_config) in components_config.items():
    try:
        component = init_component(component_config)
        components[name] = component
    except Exception as e:
        print(f"Component '{name}' failed to initialize with exception: {e} ({type(e)})")

subscriptions = []
for (name, component) in components.items():
    subscriptions.append({"component": component, "component_subscriptions": component.get_subscriptions()})

packet_manager = get_packet_manager()
packet_manager.node = node_id
packet_manager.subscriptions = subscriptions

node = Node(components, packet_manager)

while True:
    node.process()
