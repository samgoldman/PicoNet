import usb_cdc
import microcontroller

usb_cdc.enable(console=True, data=True)
print("Boot reason:", microcontroller.cpu.reset_reason)