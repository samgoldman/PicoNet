
from busio import SPI
from pin_map import get_pin

class PeripheralManager():
    peripherals: dict = {}

    def __init__(self, params):
        # TODO
        pass

    def initialize_peripheral(self, name, config) -> bool:
        if config["type"] == "SPI":
            cipo = get_pin(config["cipo"])
            copi = get_pin(config["copi"])
            sck  = get_pin(config["sck"])

            self.peripherals[name] = SPI(sck, copi, cipo)
            return True

        return False

    def get_peripheral(self, name):
        return self.peripherals[name]

_manager_instance: PeripheralManager = None

def get_peripheral_manager(params=None) -> PeripheralManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PeripheralManager(params)
    return _manager_instance
