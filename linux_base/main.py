import serial
import struct
import sys
import json
import paho.mqtt.client as mqtt

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

def on_message(client, userdata, msg):
    if msg.topic == "/led_strips/cmd":
        cmd = json.loads(msg.payload.decode("utf-8"))
        pico_cmd = generate_led_strip_command(cmd["node"], 1, cmd["cmd"], cmd["value"])
        ser.write(pico_cmd)
    if msg.topic == "/led_strips_commander/shutdown":
        ser.close()
        exit()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)

    client.subscribe("/led_strips/#")
    client.subscribe("/led_strips_commander/#")


client = mqtt.Client(client_id="linux_led_strip_client_0")
client.on_connect = on_connect
client.on_message = on_message

client.connect("10.0.0.31", 1883, 60)


client.loop_forever()
# ser.close()
