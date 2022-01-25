import time
import adafruit_logging
from component import Component
from packet import Packet
import os
from crc import crc32
from math import ceil

from packet_manager import PACKET_TYPE_ACK_REQUESTED, PACKET_TYPE_DATA, get_packet_manager

TYPE_FILE_MANAGER = 0x04

COMMAND_NOOP     = 0x00
# Upload commands
COMMAND_RESET    = 0x01
COMMAND_APPEND   = 0x02
COMMAND_SAVE     = 0x03
# File manipulation commands
COMMAND_REMOVE   = 0x04
COMMAND_RENAME   = 0x05
# Download commands
COMMAND_DOWNLOAD = 0x06

RESPONSE_OK       = 0x07
RESPONSE_READONLY = 0x08
RESPONSE_NOFILE   = 0x09

COMMAND_INITIATE_DOWNLOAD = 0x0A

# Payload formatting:
# Byte      0: command/response
# Byte      1: transaction id
# Bytes   2-5: seq (counter)
# Byte      6: len
# Bytes  7-42: data (max 36 bytes)
# Bytes 43-46: crc

MAX_DATA_PER_PACKET = 36

def convert_null_terminated_str(byte_str: bytes):
    end = len(byte_str)
    for i in range(len(byte_str)):
        if byte_str[i] == 0:
            end = i
            break

    return (byte_str[0:end].decode('utf-8'), end)

class FileManager(Component):
    ongoing_file_sends = {}
    ongoing_file_receptions = {}

    def __init__(self, params: dict):
        self.root = params["root"]
        self.node = params["node"]
        self.logger = adafruit_logging.getLogger('logger')

    def run_periodic(self):
        pass

    def process_packet(self, packet: Packet):
        if packet.payload[0] == RESPONSE_NOFILE:
            self.logger.info("File manager go response 'NOFILE'")
        if packet.payload[0] == COMMAND_REMOVE:
            (filename, _) = convert_null_terminated_str(packet.payload[1:])

            search_dir = self.root + os.sep.join(filename.split(os.sep)[0:-1])
            if not (filename.split(os.sep)[-1] in os.listdir(search_dir)):
                get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                  None,
                                                                  packet.origin,
                                                                  0,
                                                                  0x04,
                                                                  0,
                                                                  bytes([RESPONSE_NOFILE, 0x00]) + b'\x00'*45,
                                                                  origin=packet.destination))
            os.remove(self.root + filename)
        if packet.payload[0] == COMMAND_SAVE:
            transaction_id = packet.payload[1]
            crc = int.from_bytes(packet.payload[2:6], 'little')
            (filename, _) = convert_null_terminated_str(packet.payload[6:])

            with(open(self.root + filename, 'wb')) as f:
                f.write(self.ongoing_file_receptions[transaction_id])
            
            self.ongoing_file_receptions[transaction_id] = b''

        if packet.payload[0] == COMMAND_APPEND:
            transaction_id = packet.payload[1]
            seq = int.from_bytes(packet.payload[2:6], 'little')
            num_bytes = packet.payload[6]
            data = packet.payload[7:7+num_bytes]
            crc = int.from_bytes(packet.payload[43:], 'little')

            if not transaction_id in self.ongoing_file_receptions:
                self.ongoing_file_receptions[transaction_id] = b''

            self.ongoing_file_receptions[transaction_id] += data

        if packet.payload[0] == COMMAND_INITIATE_DOWNLOAD:
            transaction_id = os.urandom(1)
            destination = packet.payload[2]
            params = packet.payload[3:]

            payload = bytes([COMMAND_DOWNLOAD]) + transaction_id + params

            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA | PACKET_TYPE_ACK_REQUESTED,
                                                                None,
                                                                destination,
                                                                0,
                                                                0x04,
                                                                0,
                                                                payload))
        if packet.payload[0] == COMMAND_DOWNLOAD:
            transaction_id = packet.payload[1]
            params = packet.payload[2:]
            (src_filename, end) = convert_null_terminated_str(params)
            (dst_filename, end2) = convert_null_terminated_str(params[end + 1:])

            search_dir = self.root + os.sep.join(src_filename.split(os.sep)[0:-1])
            if not (src_filename.split(os.sep)[-1] in os.listdir(search_dir)):
                get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                  None,
                                                                  packet.origin,
                                                                  0,
                                                                  0x04,
                                                                  0,
                                                                  bytes([RESPONSE_NOFILE, transaction_id]) + b'\x00'*45,
                                                                  origin=packet.destination))
            else:
                with open(self.root + src_filename, 'rb') as fin:
                    transaction_id = int.from_bytes(os.urandom(1), 'little')
                    filedata = fin.read()
                    filesize = len(filedata)

                    packet_count = ceil(filesize / float(MAX_DATA_PER_PACKET))

                    for i in range(packet_count):
                        lower_bound = i * MAX_DATA_PER_PACKET
                        upper_bound = min(filesize, i * MAX_DATA_PER_PACKET + MAX_DATA_PER_PACKET)
                        data = filedata[lower_bound:upper_bound]
                        crc = crc32(data)
                        byte_count = len(data)
                        if byte_count < MAX_DATA_PER_PACKET:
                            data += b'\x00' * (MAX_DATA_PER_PACKET - byte_count)
                        assert(byte_count <= MAX_DATA_PER_PACKET)

                        try:
                            payload = bytes([COMMAND_APPEND, transaction_id]) + int.to_bytes(i, 4, 'little') + bytes([byte_count]) + data + int.to_bytes(crc, 4, 'little')

                            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                            None,
                                                                            packet.origin,
                                                                            0,
                                                                            0x04,
                                                                            0,
                                                                            payload,
                                                                            origin=packet.destination))
                        except:
                            pass

                    full_crc = crc32(filedata)
                    get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                        None,
                                                                        packet.origin,
                                                                        0,
                                                                        0x04,
                                                                        0,
                                                                        bytes([COMMAND_SAVE, transaction_id]) + 
                                                                          int.to_bytes(full_crc, 4, 'little') + 
                                                                          bytes(dst_filename, 'utf-8'),
                                                                        origin=packet.destination))

    def get_subscriptions(self):
        return [{"device_type": TYPE_FILE_MANAGER, "device_id": 0}]
