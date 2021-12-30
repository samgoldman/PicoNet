import serial
import struct
import sys
import time

TYPE_LED_STRIP = 0x02
### COMMMANDS ###
NOOP      = 0x00
SET_RED   = 0x01
SET_GREEN = 0x02
SET_BLUE  = 0x03
SET_ALL   = 0x04
#################

def generate_led_strip_command(node, device_id, command, value):
    PACKING_FORMAT = "<BBBBIBBBH47s"
    data = struct.pack(PACKING_FORMAT, 0, 
                                       0, 
                                       0, 
                                       node, 
                                       0, 
                                       TYPE_LED_STRIP, 
                                       device_id,
                                       command,
                                       value,
                                       b'\x00'*47)
    assert(len(data) == 60)

    return data


ser = serial.Serial("/dev/ttyACM1")

cmd = generate_led_strip_command(int(sys.argv[1]), 1, int(sys.argv[2]), int(sys.argv[3]))

print(ser.write(cmd))

ser.close()
