import time
import adafruit_logging
from component import Component
from packet import Packet
import os
from crc import crc32
from math import ceil

from packet_manager import PACKET_TYPE_ACK_REQUESTED, PACKET_TYPE_DATA, get_packet_manager
from utils import str_to_log_val

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
RESPONSE_ACK      = 0x0B

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

class OutboundTransaction():
    logger_: adafruit_logging.Logger
    file_ = None
    last_packet_: Packet
    packet_count_: int
    transaction_id_: int
    origin_: int
    destination_: int
    done_: bool
    destination_filename_: str
    save_sent_: bool

    def __init__(self, tid: int, input, origin: int, destination: int, destination_filename: str, logger: adafruit_logging.Logger):
        self.file_ = input
        self.last_packet_ = None
        self.packet_count_ = 0
        self.done_ = False
        self.transaction_id_ = tid
        self.origin_ = origin
        self.destination_ = destination
        self.destination_filename_ = destination_filename
        self.save_sent_ = False
        self.logger_ = logger

    def send_next_packet(self):
        self.logger_.debug('File Manager: Sending next packet')
        data = self.file_.read(MAX_DATA_PER_PACKET)
        
        data_byte_count = len(data)
        self.logger_.debug(f'File Manager: Read {data_byte_count} bytes for new packet')

        if data_byte_count < MAX_DATA_PER_PACKET:
            self.done_ = True
            self.logger_.debug(f'File Manager: transaction {self.transaction_id_:08x} as done')

        crc = crc32(data)

        padded_data = data + b'\x00' * (MAX_DATA_PER_PACKET - data_byte_count)

        self.packet_count_ += 1
        sequence_counter = int.to_bytes(self.packet_count_, 4, 'little')
        payload = bytes([COMMAND_APPEND, self.transaction_id_]) + sequence_counter + bytes([data_byte_count]) + padded_data + int.to_bytes(crc, 4, 'little')

        packet = Packet(PACKET_TYPE_DATA,
                        None,
                        self.destination_,
                        0,
                        0x04,
                        0,
                        payload,
                        origin=self.origin_)
        self.last_packet_ = packet
        self.last_sent_ = time.monotonic_ns()
        get_packet_manager().queue_outgoing_packet(self.last_packet_)

    def send_save(self):
        self.logger_.debug(f'File Manager: sending save for {self.transaction_id_:08x}')
        packet = Packet(PACKET_TYPE_DATA,
                        None,
                        self.destination_,
                        0,
                        0x04,
                        0,
                        bytes([COMMAND_SAVE, self.transaction_id_]) + 
                        int.to_bytes(0, 4, 'little') +  # TODO: implement full file CRC
                        bytes(self.destination_filename_, 'utf-8'),
                        origin=self.origin_)
        self.last_packet_ = packet
        self.last_sent_ = time.monotonic_ns()
        self.save_sent_ = True
        get_packet_manager().queue_outgoing_packet(self.last_packet_)

    def resend_last_packet(self):
        self.logger_.debug(f'File Manager: resending last packet for {self.transaction_id_:08x}')
        self.last_sent_ = time.monotonic_ns()
        get_packet_manager().queue_outgoing_packet(self.last_packet_)

    def resend_if_timeout(self):
        curr_time = time.monotonic_ns()
        if curr_time - self.last_sent_ >= 1000000000: # 1 sec
            self.resend_last_packet()

    def is_done(self) -> bool:
        return self.done_

    def save_sent(self) -> bool:
        return self.save_sent_

    def close(self):
        self.file_.close()
    

class FileManager(Component):
    logger: adafruit_logging.Logger
    outgoing_transactions = {}
    incoming_transactions = {}

    def __init__(self, params: dict):
        self.root = params["root"]
        self.node = params["node"]
        if "logger" in params:
            self.logger = adafruit_logging.getLogger(params["logger"]["name"])
            if "level" in params["logger"]:
                self.logger.setLevel(str_to_log_val(params["logger"]["level"]))
        else:
            self.logger = adafruit_logging.getLogger('logger')

    def run_periodic(self):
        for transaction in self.outgoing_transactions.values():
            transaction.resend_if_timeout()

    def process_packet(self, packet: Packet):
        if packet.payload[0] == RESPONSE_ACK:
            transaction_id = packet.payload[1]
            seq = int.from_bytes(packet.payload[2:6], 'little')
            self.logger.debug(f'File Manager: ACK received for {transaction_id:08x}')
            transaction: OutboundTransaction = self.outgoing_transactions[transaction_id]
            if transaction.is_done():
                if transaction.save_sent_ and seq == 0xffffffff:
                    self.logger.debug(f'File Manager: ACK received for save, closing')
                    transaction.close()
                    del self.outgoing_transactions[transaction_id]
                else:
                    self.logger.debug(f'File Manager: ACK received when done, sending save')
                    transaction.send_save()
            else:
                if seq == transaction.packet_count_:
                    self.logger.debug(f'File Manager: ACK received, not done, sending next packet')
                    transaction.send_next_packet()

        if packet.payload[0] == RESPONSE_NOFILE:
            self.logger.warning("File manager go response 'NOFILE'")
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
            _crc = int.from_bytes(packet.payload[2:6], 'little')
            (filename, _) = convert_null_terminated_str(packet.payload[6:])

            if transaction_id in self.incoming_transactions and len(self.incoming_transactions[transaction_id]["data"]) != 0:

                with(open(self.root + filename, 'wb')) as f:
                    f.write(self.incoming_transactions[transaction_id]["data"])
                
                self.incoming_transactions[transaction_id] = {
                    "data": b'',
                    "seq": 0
                }

                payload = bytes([RESPONSE_ACK, transaction_id]) + int.to_bytes(0xffffffff, 4, 'little') 
                payload += b'\x00' * (MAX_DATA_PER_PACKET - len(payload))

                get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                    None,
                                                                    packet.origin,
                                                                    0,
                                                                    0x04,
                                                                    0,
                                                                    payload))
            else:
                self.logger.warning(f"File Manager: received SAVE for non-existent transaction or empty transaction: 0x{transaction_id:02x}")

        if packet.payload[0] == COMMAND_APPEND:
            transaction_id = packet.payload[1]
            seq = int.from_bytes(packet.payload[2:6], 'little')
            num_bytes = packet.payload[6]
            data = packet.payload[7:7+num_bytes]
            expected_crc = int.from_bytes(packet.payload[43:], 'little')
            data_crc = crc32(data)

            if expected_crc == data_crc:
                if not transaction_id in self.incoming_transactions:
                    self.incoming_transactions[transaction_id] = {
                        "data": b'',
                        "seq": 0
                    }

                if (self.incoming_transactions[transaction_id]["seq"] + 1) == seq:
                    self.incoming_transactions[transaction_id]["data"] += data
                    self.incoming_transactions[transaction_id]["seq"] = seq
                else:
                    self.logger.warning(f'File Manager: rejecting out sequence packet. Packet seq={seq}; last received seq={self.incoming_transactions[transaction_id]["seq"]}')

                if self.incoming_transactions[transaction_id]["seq"] <= seq:
                    payload = bytes([RESPONSE_ACK, transaction_id]) + int.to_bytes(seq, 4, 'little')
                    payload += b'\x00' * (MAX_DATA_PER_PACKET - len(payload))

                    get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
                                                                        None,
                                                                        packet.origin,
                                                                        0,
                                                                        0x04,
                                                                        0,
                                                                        payload))

        if packet.payload[0] == COMMAND_INITIATE_DOWNLOAD:
            transaction_id = os.urandom(1)
            destination = packet.payload[2]
            params = packet.payload[3:]

            payload = bytes([COMMAND_DOWNLOAD]) + transaction_id + params

            get_packet_manager().queue_outgoing_packet(Packet(PACKET_TYPE_DATA,
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
            (dst_filename, _)   = convert_null_terminated_str(params[end + 1:])

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
                file = open(self.root + src_filename, 'rb')
                transaction_id = int.from_bytes(os.urandom(1), 'little')

                transaction = OutboundTransaction(transaction_id, file, packet.destination, packet.origin, dst_filename, self.logger)
                self.outgoing_transactions[transaction_id] = transaction
                transaction.send_next_packet()
                   

    def get_subscriptions(self):
        return [{"device_type": TYPE_FILE_MANAGER, "device_id": 0}]
