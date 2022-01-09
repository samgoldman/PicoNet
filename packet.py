import struct

PACKING_FORMAT = "<BIBBIBB47s"

class Packet():
    payload: bytes = b''
    max_payload_size: int = 47

    def get_max_payload_size():
        return 47

    def __init__(self, packet_type, packet_id, origin, destination, timestamp, payload_type, payload_device_id, payload):
        self.packet_type = packet_type
        self.packet_id = packet_id
        self.origin = origin
        self.destination = destination
        self.timestamp = timestamp
        self.payload_type = payload_type
        self.payload_device_id = payload_device_id
        self.payload = payload

    def unpack(data):
        (packet_type, 
         packet_id, 
         origin, 
         destination, 
         timestamp, 
         payload_type, 
         payload_device_id, 
         payload) = struct.unpack(PACKING_FORMAT, data)
        return Packet(packet_type, packet_id, origin, destination, timestamp, payload_type, payload_device_id, payload)

    def pack(self):
        return struct.pack(PACKING_FORMAT, self.packet_type, 
                                           self.packet_id, 
                                           self.origin, 
                                           self.destination, 
                                           self.timestamp, 
                                           self.payload_type, 
                                           self.payload_device_id, 
                                           self.payload)
