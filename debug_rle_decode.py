#!/usr/bin/env python3
"""
Debug the RLE decoder by showing raw bytes and decoded output.
We should see "SYSTEM REPORT" and "Debug" in the output.
"""

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', 2500))

print("Waiting for any packet to debug...")

while True:
    packet, addr = sock.recvfrom(4096)

    # Accept any packet size, just need the marker
    marker_pos = -1
    for marker in [b'\x11\x1f\x00\x00', b'\x08\x1f\x00\x00']:
        pos = packet.find(marker)
        if pos >= 0:
            marker_pos = pos
            break

    if marker_pos < 0:
        continue

    rle_data = packet[marker_pos+4:]

    print("=" * 80)
    print(f"Packet size: {len(packet)}, RLE size: {len(rle_data)}")
    print("=" * 80)
    print()

    # Show full RLE hex dump
    print("Full RLE data:")
    for i in range(0, len(rle_data), 16):
        hex_str = ' '.join(f'{rle_data[j]:02x}' for j in range(i, min(i+16, len(rle_data))))
        ascii_str = ''.join(chr(rle_data[j]) if 32 <= rle_data[j] < 127 else '.' for j in range(i, min(i+16, len(rle_data))))
        print(f"  [{i:3d}]: {hex_str:<48} {ascii_str}")

    print()
    print("=" * 80)
    print("MANUAL DECODE - Step by step:")
    print("=" * 80)
    print()

    # Manually decode step by step
    cursor = 0
    output_chars = []
    line_num = 0

    while cursor < len(rle_data) and line_num < 5:
        control = rle_data[cursor]
        print(f"[{cursor:3d}] Control byte: 0x{control:02x} ({control:3d})")

        if control == 0:
            print(f"      → NULL, skip")
            cursor += 1

        elif 0x01 <= control <= 0x7F:
            # Literal bytes
            literal_bytes = rle_data[cursor+1:cursor+1+control]
            literal_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02x}]' for b in literal_bytes)
            hex_str = ' '.join(f'{b:02x}' for b in literal_bytes)
            print(f"      → LITERAL {control} bytes: \"{literal_str}\"")
            print(f"         Hex: {hex_str}")
            print(f"         Output positions {len(output_chars)} to {len(output_chars)+control-1}")
            output_chars.extend(literal_bytes)
            cursor += 1 + control

        elif 0x80 <= control <= 0x8F:
            # Repeat
            count = control & 0x0F
            if cursor + 1 < len(rle_data):
                value = rle_data[cursor+1]
                val_chr = chr(value) if 32 <= value < 127 else f'[{value:02x}]'
                print(f"      → REPEAT '{val_chr}' (0x{value:02x}) {count} times")
                print(f"         Output positions {len(output_chars)} to {len(output_chars)+count-1}")
                output_chars.extend([value] * count)
                cursor += 2
            else:
                print(f"      → REPEAT but no data byte!")
                cursor += 1

        elif 0x90 <= control <= 0x9F:
            # End of line
            count = control & 0x0F
            if cursor + 1 < len(rle_data):
                attr = rle_data[cursor+1]
                print(f"      → END OF LINE (0x{control:02x}, attr=0x{attr:02x})")
                # Pad to 80 chars
                current_line_len = len(output_chars) % 80
                if current_line_len > 0:
                    padding = 80 - current_line_len
                    print(f"         Padding {padding} spaces to complete line {line_num}")
                    output_chars.extend([0x20] * padding)
                cursor += 2
                line_num += 1
                print(f"         Now at line {line_num}, total chars: {len(output_chars)}")
            else:
                cursor += 1

        else:
            print(f"      → UNKNOWN control byte!")
            cursor += 1

        print()

        # Safety limit
        if len(output_chars) > 400:
            break

    print("=" * 80)
    print("FINAL OUTPUT (HORIZONTAL - as decoded):")
    print("=" * 80)
    print()

    # Show output as lines (horizontal)
    lines = []
    for line_idx in range(min(5, len(output_chars) // 80 + 1)):
        start = line_idx * 80
        end = min(start + 80, len(output_chars))
        if start < len(output_chars):
            line_bytes = output_chars[start:end]
            line_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line_bytes)
            lines.append(line_str)
            print(f"Line {line_idx}: {line_str}")

    print()
    print("=" * 80)
    print("TRANSPOSED OUTPUT (VERTICAL - reading columns as text):")
    print("=" * 80)
    print()

    # Transpose: read vertically (column by column)
    if lines:
        max_len = max(len(line) for line in lines)
        transposed_lines = []

        for col_idx in range(max_len):
            # Read this column from all rows
            column_chars = []
            for line in lines:
                if col_idx < len(line):
                    column_chars.append(line[col_idx])
                else:
                    column_chars.append(' ')

            # Join to form the transposed line - keep ALL spaces as they are meaningful
            transposed_line = ''.join(column_chars)
            # Keep EVERY column, even if it's all spaces - spacing is important!
            transposed_lines.append(transposed_line)

        # Display each column
        for idx, tline in enumerate(transposed_lines):
            if tline.strip():  # Only print non-empty for readability
                print(f"Col {idx:2d}: '{tline}'")
            else:
                print(f"Col {idx:2d}: [space]")

        print()
        print("=" * 80)
        print("FINAL READABLE TEXT (all columns concatenated, preserving ALL spaces):")
        print("=" * 80)
        print()

        # Join columns directly - this includes all-space columns too
        readable_text = ''.join(transposed_lines)
        print(f"'{readable_text}'")

    print()
    break
