class ShowNetPacket:
    """
    Definitions for ShowNet compressed DMX packets in Python.
    This implementation handles parsing of the compressed DMX packet type only.
    """

    SHOWNET_NAME_LENGTH = 9  # Console name length
    SHOWNET_COMPRESSED_DATA_LENGTH = 1269  # Max compressed data length

    class PacketType:
        """
        Enum for packet types.
        """
        COMPRESSED_DMX_PACKET = 0x808f  # Compressed DMX packet

    class ShownetCompressedDMX:
        """
        New-style compressed DMX packet structure.
        """
        def __init__(self, net_slot, slot_size, index_block, sequence, priority, universe, password_channels, name, data):
            self.net_slot = net_slot  # Start channel of each slot (list of 4)
            self.slot_size = slot_size  # Size of each slot (list of 4)
            self.index_block = index_block  # Index into data for each slot (list of 5)
            self.sequence = sequence  # Sequence number
            self.priority = priority  # Priority (0 = not used, not used in n21+)
            self.universe = universe  # Universe (not used in n21+)
            self.password_channels = password_channels  # Channels with passwords (2 bytes)
            self.name = name  # Console name (9 characters)
            self.data = data  # Decoded DMX channel data (512 channels)

    @staticmethod
    def parse_compressed_packet(hex_string):
        """
        Parse a compressed DMX packet from a hex string.
        """
        # Convert the hex string into bytes
        raw_data = bytes.fromhex(hex_string)

        if len(raw_data) < 2:
            raise ValueError("Packet too short to determine type.")

        packet_type = int.from_bytes(raw_data[:2], byteorder='big')

        if packet_type != ShowNetPacket.PacketType.COMPRESSED_DMX_PACKET:
            raise ValueError("Not a compressed DMX packet.")

        print("Packet Type: Compressed DMX (0x808f)")

        # Extract fields sequentially, with debugging output
        net_slot = [int.from_bytes(raw_data[6 + i * 2:8 + i * 2], byteorder='big') for i in range(4)]
        print(f"Net Slot Start Channels: {net_slot}")

        slot_size = [int.from_bytes(raw_data[14 + i * 2:16 + i * 2], byteorder='big') for i in range(4)]
        print(f"Slot Sizes: {slot_size}")

        index_block = [int.from_bytes(raw_data[22 + i * 2:24 + i * 2], byteorder='big') for i in range(5)]
        print(f"Index Blocks: {index_block}")

        sequence = int.from_bytes(raw_data[30:32], byteorder='big')
        print(f"Sequence: {sequence}")

        priority = raw_data[32]
        print(f"Priority: {priority}")

        universe = raw_data[33]
        print(f"Universe: {universe}")

        password_channels = raw_data[34:36]
        print(f"Password Channels: {password_channels.hex()}")

        name = raw_data[36:36 + ShowNetPacket.SHOWNET_NAME_LENGTH].decode('ascii', errors='ignore')
        print(f"Console Name: {name}")

        # Decode channel data
        data = raw_data[36 + ShowNetPacket.SHOWNET_NAME_LENGTH:]
        print("Decoding Compressed Channel Data:")

        decoded_channels = [0] * 512  # Initialize 512 DMX channels
        channel_index = 0
        cursor = 0

        while channel_index < 512 and cursor < len(data):
            byte = data[cursor]
            cursor += 1

            if byte & 0x80:  # If the highest bit is set, it's a run of values
                num_bytes_to_read = byte & 0x7F
                print(f"Reading {num_bytes_to_read} bytes of data starting at channel {channel_index}.")

                if cursor + num_bytes_to_read > len(data):
                    raise ValueError("Not enough data to read the specified number of bytes.")

                for i in range(num_bytes_to_read):
                    decoded_channels[channel_index] = data[cursor]
                    channel_index += 1
                    cursor += 1
            else:  # If the highest bit is not set, it's a repeat instruction
                num_bytes_to_repeat = byte & 0x7F
                value_to_repeat = data[cursor]
                cursor += 1
                print(f"Repeating value {value_to_repeat} for {num_bytes_to_repeat} channels starting at {channel_index}.")

                for _ in range(num_bytes_to_repeat):
                    if channel_index >= 512:
                        break
                    decoded_channels[channel_index] = value_to_repeat
                    channel_index += 1

        print(f"Decoded DMX Channels: {decoded_channels[:64]} (first 64 channels)")  # Print the first 64 channels for brevity
        return ShowNetPacket.ShownetCompressedDMX(net_slot, slot_size, index_block, sequence, priority, universe, password_channels, name, decoded_channels)

# Example usage
#1@FF, 2@2, 3@3
hex_packet = "808f00000000010000000000000000040000000000000b00210000000000000006ad0000f401636f6e736f6c65310003ff0203ff00ff00ff00ff00ff00ff00ff00ff008500"
#1@FF, 2@2, 3@3, 4@2
hex_packet = "808f00000000010000000000000000040000000000000b00210000000000000006ad0000f401636f6e736f6c65310003ff0203ff0203ff00ff00ff00ff00ff00ff00ff00ff008500"
import shownet
#encode hex_packet as bytes
shownet.handle_packet(bytes.fromhex(hex_packet))
compressed_dmx = ShowNetPacket.parse_compressed_packet(hex_packet)
