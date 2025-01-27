from socket import *
import pprint
import logging
import sys
import struct


old_payload = ""
old_packet = ""
old_sequence = 0
sequence_packet = 0

def handle_packet(packet):
    global old_payload
    global old_packet
    global old_sequence
    global sequence_packet
    #Convert to Hex
    packet = packet.hex()
    
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
        return
    else:
        old_payload = payload
    
    loa = len(channel_values)
    cursor = 0
    iter = 0
    channel_grid = {}

    print("\n" + str(sequence).zfill(4) + ":" + str(iter) + " channel values: " + channel_values)
    
    cursor = 0
    #This works for 1 through 2 at value XX
    
    starting_channel_offset = int(channel_values[cursor:cursor+2], 16) + 1
    cursor = cursor + 2
    print("Starting Channel: " + str(starting_channel_offset).zfill(3)) 
    
   
    
    while cursor < loa:
        repeat_count = channel_values[cursor:cursor+2]
        
        print("Repeat Count: " + str(repeat_count) + " (hex) / " + str(int(repeat_count, 16)) + " (dec)")
        if int(repeat_count, 16) > 127 and channel_values[cursor:cursor+4] != "ff00":
            print("Repeat Count is greater than 127 - It is actually a starting channel")
            
            move_forward_positions = int(repeat_count, 16) - 127
            print("Need to move forward " + str(move_forward_positions) + " positions from starting_channel_offset: " + str(starting_channel_offset) + " and iter: " + str(iter))
            print("This channel should be: " + str(starting_channel_offset + move_forward_positions + iter - 1))
            starting_channel_offset = starting_channel_offset + move_forward_positions + iter -1
            iter = 0
            print("New starting_channel_offset: " + str(starting_channel_offset) + " and iter: " + str(iter))
            cursor = cursor + 2
            repeat_count = channel_values[cursor:cursor+2]
            print("Updated Repeat Count: " + str(repeat_count) + " (hex) / " + str(int(repeat_count, 16)) + " (dec)")

        if channel_values[cursor:cursor+4] == "ff00":
            print("Got FF00 - Skipping any further processing of this packet")
            cursor = cursor + 4
            return
        elif repeat_count[0:1] == "8":
            #print("Got RLE compressed data")
            repeat_count = int(repeat_count[1:2], 16)
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
            print("Got simple data - Reading the next " + str(repeat_count) + " channels one-by-one")
            cursor = cursor + 2
            repeat_count = int(repeat_count, 16)
            while repeat_count > 0:
                channel_grid[starting_channel_offset+iter] = int(channel_values[cursor:cursor+2], 16)
                iter = iter + 1
                cursor = cursor + 2
                repeat_count = repeat_count - 1
            print(channel_grid)
            print("Current Iter: " + str(iter) + " for starting_channel_offset " + str(starting_channel_offset))
            print("Remaining " + str(len(channel_values[cursor:])) + " channel values: " + channel_values[cursor:])
    
    # while cursor < loa:
    #     #if the first byte is 8 then it is RLE compressed
    #     if channel_values[cursor:cursor+3] == "008":
    #         print("RLE compressed beginning")
    #         iter = int(channel_values[cursor:cursor+2], 16)
    #         repeat_count = int(channel_values[cursor+3:cursor+4], 16)
    #         cursor = cursor + 4
            
    #         channel_value = int(channel_values[cursor:cursor+2], 16)
    #         channel_value = str(channel_value).zfill(2)
            
    #         print("Value " + str(channel_value) + " repeats: " + str(repeat_count) + " times with iter: " + str(iter))
            
    #         #Set next n number of channels to the repeated value
    #         for i in range(repeat_count):
    #             channel_grid[iter] = channel_value
    #             iter = iter + 1
    #         cursor = cursor + 2
    #         print("Channel Value: " + str(channel_value) + " is repeated " + str(repeat_count) + " times")
    #         iter = iter + 1
    #     else:
    #         #RLE Compressed continues
    #         print("RLE compressed continuing with remaining data: " + channel_values[cursor:])
            
    #         if channel_values[cursor:cursor+4] == "00ff":
    #             print("Got 00FF - Skipping")
    #             cursor = cursor + 4
    #             continue
            
    #         repeat_count = int(channel_values[cursor:cursor+2], 16)
    #         cursor = cursor + 2
    #         channel_value = int(channel_values[cursor:cursor+2], 16)
    #         channel_value = str(channel_value).zfill(2)
    #         cursor = cursor + 2
    #         print("RLE2: Value " + str(channel_value) + " repeats: " + str(repeat_count) + " times")
    #         for i in range(repeat_count):
    #             channel_grid[iter] = channel_value
    #             iter = iter + 1
    #         print(channel_grid)
    #         print("Remaining channel values: " + channel_values[cursor:])
    #         print(channel_grid)
    #         return
        

        

        
#if run as main program
if __name__ == "__main__":
    
    #Listen for broadcast packets on port 2501
    s=socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.bind(('', 2501))

    #Listen for a packet and print the contents as hex
    while True:
        packet, addr = s.recvfrom(1310)
        handle_packet(packet)
        
    