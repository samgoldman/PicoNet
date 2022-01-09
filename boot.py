import usb_cdc
import microcontroller
import os

# Boot setup

usb_cdc.enable(console=True, data=True)

# Boot checks

def file_exists_root(filename):
    return filename in os.listdir()

print("Boot reason:", microcontroller.cpu.reset_reason)

if usb_cdc.data is None:
    print("USB data serial available: NO")
else:
    print("USB data serial available: YES")

print(f"code.py found: {'YES' if file_exists_root('code.py') else 'NO'}")
print(f"config.json found: {'YES' if file_exists_root('config.json') else 'NO'}")