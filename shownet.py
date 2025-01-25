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
    channel = channel_values[cursor:cursor+4]
    channel = int(channel, 16)
    cursor += 4
    print(str(sequence).zfill(4) + ":" + str(sequence_packet).zfill(2) + " Channels: " + str(channel) + " values: ", end="")
    while cursor < loa:
        value = channel_values[cursor:cursor+2]
        cursor += 2
        iter += 1

        #Set the channel value in the grid (we add 1 as 0 is the lowest we go but channels start at 1 in DMX)
        channel_grid[str(channel)] = int(value, 16)
        
        try:
            print("\t" + str(iter).zfill(2) + ":" + str(value).zfill(2) + "(" + str(int(value, 16)).zfill(2) + ")" + " ", end="")
        except:
            print("")
        
        #if after this we get ff00 then we are at the end of the packet
        if channel_values[cursor:cursor+4] == "ff00":
            print("\nEnd of packet")
            break
        
        
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
        
    