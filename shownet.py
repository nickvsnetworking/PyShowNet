from socket import *
import pprint
import logging
import sys
import math
import struct
from stupidArtnet import StupidArtnet

# ShowNet packet constants
SHOWNET_COMPRESSED_PACKET = 0x808f
SHOWNET_DMX_PACKET = 0x202f
DMX_UNIVERSE_SIZE = 512
REPEAT_FLAG = 0x80


# ShowNet supports up to 8192 channels = 16 universes
# Initialize ArtNet universes 1-16
artnet_universes = {}
for universe in range(1, 17):
    print("Creating Artnet Universe " + str(universe))
    artnet_universes[universe] = StupidArtnet(target_ip='255.255.255.255', universe=universe, packet_size=512, fps=30, broadcast=True)


old_payload = ""
old_packet = ""
old_sequence = 0
sequence_packet = 0


def output_artnet_frame(channel_grid):
    """Convert channel grid to ArtNet universes and send.

    Args:
        channel_grid: dict mapping absolute channel numbers (1-based) to DMX values
    """
    if not channel_grid:
        return

    # Generate a DMX packet for each Artnet Universe
    dmx_packets = {}
    for universe in artnet_universes:
        dmx_packets[universe] = bytearray(512)

    # Iterate through the channel grid and populate the DMX packets
    for channel, value in channel_grid.items():
        # Calculate the correct Universe for the channel (1-based channel numbering)
        # Channels 1-512 -> Universe 1
        # Channels 513-1024 -> Universe 2
        # etc.
        universe = math.ceil(channel / 512)

        # Calculate DMX channel within the universe (0-indexed for array)
        dmx_channel = (channel - 1) % 512

        if universe not in dmx_packets:
            continue

        dmx_packets[universe][dmx_channel] = value

    # Only send universes that have non-zero data
    for universe in dmx_packets:
        if any(dmx_packets[universe]):
            artnet_universes[universe].set(dmx_packets[universe])
            artnet_universes[universe].show()

def decode_rle(data, data_offset, enc_len, start_channel):
    """Decode RLE-compressed DMX data.

    Args:
        data: byte array containing RLE data
        data_offset: offset into data where RLE starts
        enc_len: length of encoded data
        start_channel: starting DMX channel number

    Returns:
        dict mapping channel numbers to values
    """
    channel_grid = {}
    cursor = data_offset
    end = data_offset + enc_len
    current_channel = start_channel

    while cursor < end:
        control_byte = data[cursor]
        segment_length = control_byte & (~REPEAT_FLAG)  # Lower 7 bits

        if control_byte & REPEAT_FLAG:  # Repeat mode (bit 7 set)
            cursor += 1
            if cursor >= end:
                break
            value = data[cursor]
            cursor += 1
            for i in range(segment_length):
                channel_grid[current_channel + i] = value
            current_channel += segment_length
        else:  # Literal mode
            cursor += 1
            if cursor + segment_length > end:
                break
            for i in range(segment_length):
                channel_grid[current_channel + i] = data[cursor + i]
            cursor += segment_length
            current_channel += segment_length

    return channel_grid

def handle_packet(packet):
    global old_payload
    global old_packet
    global old_sequence
    global sequence_packet

    # Parse packet header (type + IP)
    if len(packet) < 6:
        return

    # Unpack type field (BIG-ENDIAN/network byte order uint16)
    packet_type = struct.unpack('>H', packet[0:2])[0]

    if packet_type != SHOWNET_COMPRESSED_PACKET:
        return

    # Parse compressed DMX packet header
    # struct shownet_compressed_dmx_s {
    #   uint16_t netSlot[4];       // offset 6: start channel of each slot
    #   uint16_t slotSize[4];      // offset 14: size of each slot
    #   uint16_t indexBlock[5];    // offset 22: index into data of each slot
    #   uint16_t sequence;         // offset 32
    #   uint8_t priority;          // offset 34
    #   uint8_t universe;          // offset 35
    #   uint8_t pass[2];           // offset 36
    #   char name[9];              // offset 38
    #   uint8_t data[1269];        // offset 47: RLE data
    # }

    HEADER_OFFSET = 6
    if len(packet) < HEADER_OFFSET + 47:
        print(f"Packet too short for compressed header: {len(packet)} bytes")
        return

    # Parse header fields (all little-endian uint16)
    net_slot = struct.unpack('<4H', packet[HEADER_OFFSET:HEADER_OFFSET+8])
    slot_size = struct.unpack('<4H', packet[HEADER_OFFSET+8:HEADER_OFFSET+16])
    index_block = struct.unpack('<5H', packet[HEADER_OFFSET+16:HEADER_OFFSET+26])
    sequence = struct.unpack('<H', packet[HEADER_OFFSET+26:HEADER_OFFSET+28])[0]
    priority = packet[HEADER_OFFSET+28]
    universe_field = packet[HEADER_OFFSET+29]
    pass_field = packet[HEADER_OFFSET+30:HEADER_OFFSET+32]

    # Data starts at offset 47 from header start (6 + 47 = 53 from packet start)
    # (Name field is 9 bytes at offset 32, but we don't need to parse it)
    data_start = HEADER_OFFSET + 41

    # Track sequence for duplicate detection
    if old_sequence != sequence:
        sequence_packet = 0
    else:
        sequence_packet = sequence_packet + 1
    old_sequence = sequence

    # Process only the first slot (like OLA does)
    # We could process all 4 slots, but for now match OLA behavior
    if net_slot[0] == 0 or slot_size[0] == 0:
        return

    # Magic offset constant - in the ShowNet spec, the pass(2) and name(9) fields
    # are combined with the compressed data, so indices are off by 11
    MAGIC_INDEX_OFFSET = 11

    if index_block[0] < MAGIC_INDEX_OFFSET:
        return

    # Calculate the actual offset into the data array
    data_offset = data_start + (index_block[0] - MAGIC_INDEX_OFFSET)

    # Calculate encoded data length
    enc_len = index_block[1] - index_block[0]

    if enc_len < 1:
        return

    if data_offset + enc_len > len(packet):
        return

    # Calculate starting channel from netSlot
    # netSlot is 1-based channel number across all universes
    start_channel = (net_slot[0] - 1) % DMX_UNIVERSE_SIZE

    # Check if data is RLE compressed or raw
    # If slotSize != encoded length, it's RLE compressed
    if slot_size[0] != enc_len:
        channel_grid = decode_rle(packet, data_offset, enc_len, start_channel)
    else:
        channel_grid = {}
        for i in range(enc_len):
            channel_grid[start_channel + i] = packet[data_offset + i]

    # Convert relative channels to absolute channel numbers
    # channel_grid has channels relative to start_channel (0-based offset)
    # netSlot[0] tells us the absolute starting channel (1-based)
    # So absolute channel = netSlot[0] + relative_channel
    channel_grid_absolute = {}
    for ch, val in channel_grid.items():
        absolute_channel = net_slot[0] + ch
        channel_grid_absolute[absolute_channel] = val

    # Only print if there are non-zero channels
    non_zero = [(ch, val) for ch, val in channel_grid_absolute.items() if val != 0]
    if non_zero:
        print(f"\nShowNet packet received:")
        print(f"  Channels {net_slot[0]}-{net_slot[0] + len(channel_grid) - 1}")
        print(f"  Non-zero values ({len(non_zero)}):")
        for ch, val in non_zero[:20]:  # Show first 20 non-zero
            print(f"    Ch {ch} = {val}")
        if len(non_zero) > 20:
            print(f"    ... and {len(non_zero) - 20} more")

    output_artnet_frame(channel_grid_absolute)


        

        
#if run as main program
if __name__ == "__main__":
    
    #Listen for broadcast packets on port 2501
    s=socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.bind(('', 2501))
    print("Bound to port 2501")
    #Listen for a packet and print the contents as hex
    
    print("Listening for packets...")
    while True:
        packet, addr = s.recvfrom(1310)
        handle_packet(packet)
        
    