from socket import *
import pprint
import logging
import sys


import struct

# Constants
SHOWNET_NAME_LENGTH = 9
SHOWNET_COMPRESSED_DATA_LENGTH = 1269

class ShowNetCompressedDMX:
    def __init__(self, netSlot, slotSize, indexBlock, sequence, priority, universe, pass_, name, data):
        self.netSlot = netSlot            # List of 4 uint16_t
        self.slotSize = slotSize          # List of 4 uint16_t
        self.indexBlock = indexBlock      # List of 5 uint16_t
        self.sequence = sequence          # uint16_t
        self.priority = priority          # uint8_t
        self.universe = universe          # uint8_t
        self.pass_ = pass_                # List of 2 uint8_t
        self.name = name                  # SHOWNET_NAME_LENGTH bytes
        self.data = self._convert_hex_to_bytes(data) if isinstance(data, str) else data

    def _convert_hex_to_bytes(self, hex_string):
        """
        Convert a hex string to bytes. Pads with zeros if the string is shorter than the required length.
        """
        try:
            data = bytes.fromhex(hex_string)
            if len(data) > SHOWNET_COMPRESSED_DATA_LENGTH:
                raise ValueError(f"Hex string too long (max {SHOWNET_COMPRESSED_DATA_LENGTH} bytes)")
            return data.ljust(SHOWNET_COMPRESSED_DATA_LENGTH, b'\x00')  # Pad with zeros if too short
        except ValueError:
            raise ValueError("Invalid hex string format")

    def pack(self):
        fmt = '<4H 4H 5H H B B 2B {}s {}s'.format(SHOWNET_NAME_LENGTH, SHOWNET_COMPRESSED_DATA_LENGTH)
        return struct.pack(
            fmt,
            *self.netSlot,
            *self.slotSize,
            *self.indexBlock,
            self.sequence,
            self.priority,
            self.universe,
            *self.pass_,
            self.name.encode('ascii'),
            self.data
        )

    @classmethod
    def unpack(cls, buffer):
        fmt = '<4H 4H 5H H B B 2B {}s {}s'.format(SHOWNET_NAME_LENGTH, SHOWNET_COMPRESSED_DATA_LENGTH)
        unpacked = struct.unpack(fmt, buffer)
        return cls(
            netSlot=unpacked[0:4],
            slotSize=unpacked[4:8],
            indexBlock=unpacked[8:13],
            sequence=unpacked[13],
            priority=unpacked[14],
            universe=unpacked[15],
            pass_=unpacked[16:18],
            name=unpacked[18].decode('ascii').rstrip('\x00'),
            data=unpacked[19]
        )


#Listen for broadcast packets on port 2501
s=socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.bind(('', 2501))
#s.listen(1)
old_payload = ""
old_packet = ""
old_sequence = 0
sequence_packet = 0
#Listen for a packet and print the contents as hex
while True:
    packet, addr = s.recvfrom(1310)
    # print('Received packet from: ', addr)
    # print('Packet contents: ', packet)
    # #Convert the packet to hex and print it
    #print('Packet contents (hex): ', packet.hex())
    
    #print('Packet Length: ', len(packet))
    packet_bytes = packet
    packet = packet.hex()
    
    if packet[0:4] == "808f":
        pass
    elif packet[0:4] == "202f":
        pass
    else:
        print("Unknown")
        continue

    sequence = packet[65:67]
    #convert sequence to decimal from hex
    sequence = int(sequence, 16)
        
    if old_sequence != sequence:
        sequence_packet = 0
        payload_data = ''
    else:
        sequence_packet = sequence_packet + 1
        payload_data += packet[68:]
    old_sequence = sequence
    print("Sequence: " + str(sequence).zfill(2) + ":" + str(sequence_packet).zfill(2) + " payload data length: " + str(len(payload_data)))


    if len(payload_data) > 1000:
        
        unpacked_data = ShowNetCompressedDMX.unpack(payload_data)
        print("Unpacked Data:")
        print(f"  netSlot: {unpacked_data.netSlot}")
        print(f"  slotSize: {unpacked_data.slotSize}")
        print(f"  indexBlock: {unpacked_data.indexBlock}")
        print(f"  sequence: {unpacked_data.sequence}")
        print(f"  priority: {unpacked_data.priority}")
        print(f"  universe: {unpacked_data.universe}")
        print(f"  pass_: {unpacked_data.pass_}")
        print(f"  name: {unpacked_data.name}")
        print(f"  data (hex): {unpacked_data.data.hex()}")

    
    #Payload is everything after sequence number
    payload = packet[68:]
    
    
    channel_values = payload[24:]
    
    if payload == old_payload:
        continue
    else:
        old_payload = payload
    
    # print("\n" + str(sequence).zfill(4) + ":" + str(iter) + " channel values: " + channel_values)
    # loa = len(channel_values)
    # cursor = 0
    # iter = 0
    # channel = channel_values[cursor:cursor+4]
    # cursor += 4
    # print(str(sequence).zfill(4) + ":" + str(sequence_packet).zfill(2) + " Channel: " + str(channel) + " values: ", end="")
    # while cursor < loa:
    #     value = channel_values[cursor:cursor+2]
    #     cursor += 2
    #     iter += 1
        
    #     if iter > 10:
    #         break
        
    #     #Current theory - This counts unique values of the DMX channels.
    
    #     try:
    #         print("\t" + str(iter).zfill(2) + ":" + str(value).zfill(2) + "(" + str(int(value, 16)).zfill(2) + ")" + " ", end="")
    #     except:
    #         print("")
    #         continue
    