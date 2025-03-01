from socket import *
import pprint
import logging
import sys
import math
import struct
from stupidArtnet import StupidArtnet


universe = 1
artnet_universes = {}
while universe < 8:
    print("Creating Artnet Universe " + str(universe))
    artnet_universes[universe] = StupidArtnet(target_ip='255.255.255.255', universe=universe, packet_size=512, fps=30, broadcast=True)
    universe = universe + 1


old_payload = ""
old_packet = ""
old_sequence = 0
sequence_packet = 0


def output_artnet_frame(channel_grid):
    #Fill in gaps in channel grid between values
    last_channel = 0
    channel_grid = dict(sorted(channel_grid.items()))
    channel_grid_filled = {}
    for channel in channel_grid:
        if channel - last_channel > 1:
            for i in range(last_channel+1, channel):
                channel_grid_filled[i] = 0
        channel_grid_filled[channel] = channel_grid[channel]
        last_channel = channel
        
    #pprint.pprint(channel_grid_filled)

    #Generate a DMX packet for each Artnet Universe
    dmx_packets = {}
    for universe in artnet_universes:
        dmx_packets[universe] = bytearray(512)
    
    #iterate through the channel grid and populate the DMX packets
    for channel in channel_grid_filled:
        #Calculate the correct Universe for the channel by dividing by 512 and rounding up
        universe = math.ceil(channel/512)
        dmx_channel = channel - ((universe-1)*512)
        #print("Setting DMX Channel " + str(universe) + ":" + str(dmx_channel) + " to " + str(channel_grid_filled[channel]))
        dmx_packets[universe][channel-(512*universe)-1] = channel_grid_filled[channel]
    
    print("Sending DMX packets")
    #pprint.pprint(dmx_packets)
    
    for universe in dmx_packets:
        artnet_universes[universe].set(dmx_packets[universe])
        artnet_universes[universe].show()

def handle_packet(packet):
    global old_payload
    global old_packet
    global old_sequence
    global sequence_packet
    #Convert to Hex
    packet = packet.hex()
    print('\n\n')
    if packet[0:4] == "808f":
        pass
    else:
        print("Unknown packet type")
        return

    sequence = packet[65:67]
    #convert sequence to decimal from hex
    sequence = int(sequence, 16)
        
    #Payload is everything after sequence number
    payload = packet[68:]

    if old_sequence != sequence:
        sequence_packet = 0
    else:
        sequence_packet = sequence_packet + 1
    old_sequence = sequence
    print("Sequence: " + str(sequence).zfill(2) + ":" + str(sequence_packet).zfill(2) + " payload: " + str(len(payload)))
    
    
    channel_values = payload[24:]
    
    if payload == old_payload:
        print("Duplicate packet")
        # artnet_universe_a.set(dmx_packet)
        # artnet_universe_a.show()
        return
    else:
        old_payload = payload
    
    loa = len(channel_values)
    cursor = 0
    iter = 0
    universe = 1
    channel_grid = {}

    print("\n" + str(sequence).zfill(4) + ":" + str(iter) + " channel values: " + channel_values)
    
    cursor = 0
    #This works for 1 through 2 at value XX
    
    starting_channel_offset = int(channel_values[cursor:cursor+2], 16) + 1
    cursor = cursor + 2
    print("Starting Channel: " + str(starting_channel_offset).zfill(3)) 
    
#Channel 1337 at almost full (fe)
#00ff00ff00ba0001fe ba = 186
#00ff00ff00ba0001e9 ba = 186
#Current thinking:
#Channel 1337 is at Universe 3 (512 + 512 + 313)
#313 - 127 = 186
    
    while cursor < loa:
        RLE_Encoded = False

        repeat_count = channel_values[cursor:cursor+2]

        if repeat_count[0:1] == "8":
            RLE_Encoded = True
        
        print("Repeat Count: " + str(repeat_count) + " (hex) / " + str(int(repeat_count, 16)) + " (dec)")
        
        #Need to determine how we know if the channel is an RLE compressed channel or a starting channel
        
        if int(repeat_count, 16) > 127 and repeat_count[0:1] != "8" and channel_values[cursor:cursor+4] != "ff00":
            print("Repeat Count is greater than 127 - It is actually a starting channel")
            #This is a RLE compressed channel
            repeat_count = int(repeat_count, 16) - 128
            print("128: Got RLE compressed data with repeat count: " + str(repeat_count) + " (int)")
            #Convert back to hex
            repeat_count = format(repeat_count, 'x')
            print("128: Got RLE compressed data with repeat count: " + str(repeat_count) + " (hex)")
            RLE_Encoded = True
        if channel_values[cursor:cursor+4] == "ff00":
            print("\n\nGot FF00 - Skipping ahead - Current channel: " + str(starting_channel_offset+iter))
            cursor = cursor + 4
            #Iterate through the channels until we hit a non-FF00 channel
            blocks = 1
            while channel_values[cursor:cursor+4] == "ff00":
                print("\t Skipping another FF00 channel")
                iter = iter + 1
                cursor = cursor + 4
                blocks += 1
            print("Finished skipping FF00 channels, found " + str(blocks) + " blocks")
                        
            print("Current Iter: " + str(iter) + " for starting_channel_offset " + str(starting_channel_offset))
            
            starting_channel_offset = ((126*blocks) + iter + 2)
            print("New starting channel: " + str(starting_channel_offset))
            iter = 0
            
            print("Remaining " + str(len(channel_values[cursor:])) + " bytes of channel values: " + channel_values[cursor:])

            #if we've only got 4 bytes left, we're at the end of the packet
            if len(channel_values[cursor:]) <= 4:
                print("End of packet")
                print(channel_grid)
                output_artnet_frame(channel_grid)
                return
            if starting_channel_offset+iter > 700:
                print("Too many channels")
                print(channel_grid)
                return
        elif RLE_Encoded:
            #print("Got RLE compressed data")
            if repeat_count[0:1] == "8":
                repeat_count = int(repeat_count[1:2], 16)
            else:
                repeat_count = int(repeat_count, 16)
            cursor = cursor + 2
            channel_value = int(channel_values[cursor:cursor+2], 16)
            cursor = cursor + 2
            print("RLE compressed data repeats: " + str(repeat_count) + " times with value " + str(channel_value))
            while repeat_count > 0:
                channel_grid[starting_channel_offset+iter] = channel_value
                iter = iter + 1
                repeat_count = repeat_count - 1
            print(channel_grid)
            print("Current Iter: " + str(iter) + " for starting_channel_offset " + str(starting_channel_offset))
            print("Remaining " + str(len(channel_values[cursor:])) + " channel values: " + channel_values[cursor:])
        else:
            #Convert to decimal
            print("Got simple data with repeat count: " + str(repeat_count))
            repeat_count = int(str(repeat_count), 16)
            print("Got simple data - Reading the next " + str(repeat_count) + " channels one-by-one in position " + str(starting_channel_offset+iter))
            cursor = cursor + 2
            while repeat_count > 0:
                channel_grid[starting_channel_offset+iter] = int(channel_values[cursor:cursor+2], 16)
                iter = iter + 1
                cursor = cursor + 2
                repeat_count = repeat_count - 1
            print(channel_grid)
            print("Current Iter: " + str(iter) + " for starting_channel_offset " + str(starting_channel_offset))
            print("Remaining " + str(len(channel_values[cursor:])) + " channel values: " + channel_values[cursor:])
            if (starting_channel_offset+iter) > 700:
                print("Too many channels")
                print(channel_grid)
                sys.exit()


        

        
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
        
    