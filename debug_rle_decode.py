#!/usr/bin/env python3
"""
Debug the RLE decoder by showing raw bytes and decoded output.
We should see "SYSTEM REPORT" and "Debug" in the output.
"""

import socket

# ANSI color codes for VGA attributes
ANSI_COLORS = {
    # Foreground colors (30-37 normal, 90-97 bright)
    0: '\033[30m',   # Black
    1: '\033[34m',   # Blue
    2: '\033[32m',   # Green
    3: '\033[36m',   # Cyan
    4: '\033[31m',   # Red
    5: '\033[35m',   # Magenta
    6: '\033[33m',   # Brown/Yellow
    7: '\033[37m',   # White
    8: '\033[90m',   # Gray (bright black)
    9: '\033[94m',   # Light Blue
    10: '\033[92m',  # Light Green
    11: '\033[96m',  # Light Cyan
    12: '\033[91m',  # Light Red
    13: '\033[95m',  # Light Magenta
    14: '\033[93m',  # Yellow (bright)
    15: '\033[97m',  # Bright White
}

BG_COLORS = {
    # Background colors (40-47)
    0: '\033[40m',   # Black
    1: '\033[44m',   # Blue
    2: '\033[42m',   # Green
    3: '\033[46m',   # Cyan
    4: '\033[41m',   # Red
    5: '\033[45m',   # Magenta
    6: '\033[43m',   # Brown/Yellow
    7: '\033[47m',   # White
}

RESET = '\033[0m'

def vga_to_ansi(attr):
    """Convert VGA attribute byte to ANSI color codes."""
    fg = attr & 0x0F
    bg = (attr >> 4) & 0x07
    # blink = (attr >> 7) & 0x01  # We'll ignore blink for now

    fg_code = ANSI_COLORS.get(fg, '')
    bg_code = BG_COLORS.get(bg, '')

    return fg_code + bg_code

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', 2500))

print("Waiting for any packet to debug...")

while True:
    packet, addr = sock.recvfrom(4096)
    print(f"Packet received: {len(packet)} bytes from {addr}")

    # Show first 200 bytes to see what we got
    print("First 200 bytes:")
    for i in range(0, min(200, len(packet)), 16):
        hex_str = ' '.join(f'{packet[j]:02x}' for j in range(i, min(i+16, len(packet))))
        print(f"  [{i:4d}]: {hex_str}")

    # Marker is always at offset 164
    marker_pos = 164

    if len(packet) < 168:
        print(f"Packet too short: {len(packet)} bytes")
        continue

    marker_found = packet[marker_pos:marker_pos+4]
    print(f"Marker at {marker_pos}: {marker_found.hex()}")

    header_data = packet[0:marker_pos]
    rle_data = packet[marker_pos+4:]

    print("=" * 80)
    print(f"Packet size: {len(packet)}, Header size: {len(header_data)}, RLE size: {len(rle_data)}")
    print(f"Marker position: {marker_pos}")
    print("=" * 80)
    print()

    # Show unused header bytes with position and decimal value
    print("=" * 80)
    print("UNUSED HEADER BYTES (before RLE marker):")
    print("=" * 80)
    print()

    # Show hex dump with 16 bytes per line
    for i in range(0, len(header_data), 16):
        hex_str = ' '.join(f'{header_data[j]:02x}' for j in range(i, min(i+16, len(header_data))))
        ascii_str = ''.join(chr(header_data[j]) if 32 <= header_data[j] < 127 else '.' for j in range(i, min(i+16, len(header_data))))
        print(f"  [{i:4d}]: {hex_str:<48} {ascii_str}")

    print()
    print("DETAILED VIEW - Position and Decimal Value for each byte:")
    print()

    # Show each byte with position, hex, and decimal
    for i in range(len(header_data)):
        value = header_data[i]
        ascii_char = chr(value) if 32 <= value < 127 else '.'

        # Highlight interesting positions
        note = ""
        if i == 0 or i == 1:
            note = " <- Packet type/magic"
        elif i == 13:
            note = " <- Display width?"
        elif i == 16:
            note = " <- Packet size?"
        elif i == 30:
            note = " <- LINE NUMBER (likely)"
        elif i == 96:
            note = " <- Unknown field"

        # Only print non-zero bytes or important positions
        if value != 0 or note:
            print(f"  Pos[{i:3d}]: 0x{value:02x} = {value:3d}  '{ascii_char}'{note}")

    print()
    print("KEY HEADER FIELDS:")
    if len(header_data) >= 2:
        print(f"  Offset   0-1 : 0x{header_data[0]:02x}{header_data[1]:02x} - Likely packet type/magic")
    if len(header_data) >= 14:
        print(f"  Offset    13 : {header_data[13]:3d} (0x{header_data[13]:02x}) - Likely display width (80 chars?)")
    if len(header_data) >= 17:
        print(f"  Offset    16 : {header_data[16]:3d} (0x{header_data[16]:02x}) - Likely packet size")
    if len(header_data) >= 31:
        print(f"  Offset    30 : {header_data[30]:3d} (0x{header_data[30]:02x}) - LIKELY LINE NUMBER (1-indexed)")
    if len(header_data) >= 97:
        print(f"  Offset    96 : {header_data[96]:3d} (0x{header_data[96]:02x}) - Unknown (cursor pos?)")

    # Count non-zero bytes in header
    non_zero_count = sum(1 for b in header_data if b != 0)
    print(f"  Non-zero bytes in header: {non_zero_count}/{len(header_data)}")

    # Analyze color/attribute region (offsets 60-84)
    if len(header_data) >= 85:
        print()
        print("COLOR/ATTRIBUTE REGION (offsets 60-84, likely line colors):")
        attr_region = header_data[60:85]
        unique_attrs = sorted(set(attr_region))

        # Decode VGA-style attributes
        fg_colors = ["Blk", "Blu", "Grn", "Cyn", "Red", "Mag", "Brn", "Wht",
                     "Gry", "LBlu", "LGrn", "LCyn", "LRed", "LMag", "Yel", "BWht"]
        bg_colors = ["Blk", "Blu", "Grn", "Cyn", "Red", "Mag", "Brn", "Wht"]

        if len(unique_attrs) == 1:
            attr = unique_attrs[0]
            fg = attr & 0x0F
            bg = (attr >> 4) & 0x07
            blink = (attr >> 7) & 0x01
            color_desc = f"{fg_colors[fg]} on {bg_colors[bg]}"
            if blink:
                color_desc += " (BLINK)"
            print(f"  All 25 bytes are 0x{attr:02x} = {color_desc}")
        else:
            print(f"  Multiple attribute values found: {[f'0x{a:02x}' for a in unique_attrs]}")
            for i, attr in enumerate(attr_region):
                if attr != 0x07:  # Only show non-standard
                    fg = attr & 0x0F
                    bg = (attr >> 4) & 0x07
                    print(f"    Line {i}: 0x{attr:02x} = {fg_colors[fg]}/{bg_colors[bg]}")

    print()
    print("=" * 80)

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

                # Decode VGA-style attribute
                fg = attr & 0x0F
                bg = (attr >> 4) & 0x07
                blink = (attr >> 7) & 0x01
                fg_colors = ["Blk", "Blu", "Grn", "Cyn", "Red", "Mag", "Brn", "Wht",
                             "Gry", "LBlu", "LGrn", "LCyn", "LRed", "LMag", "Yel", "BWht"]
                bg_colors = ["Blk", "Blu", "Grn", "Cyn", "Red", "Mag", "Brn", "Wht"]
                color_desc = f"{fg_colors[fg]}/{bg_colors[bg]}"
                if blink:
                    color_desc += " BLINK"

                print(f"      → END OF LINE (0x{control:02x}, attr=0x{attr:02x} = {color_desc})")
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

    # Collect line attributes from the RLE decode
    line_attributes = []
    cursor_temp = 0
    while cursor_temp < len(rle_data):
        control = rle_data[cursor_temp]
        if control == 0:
            cursor_temp += 1
        elif 0x01 <= control <= 0x7F:
            if cursor_temp + 1 + control <= len(rle_data):
                cursor_temp += 1 + control
            else:
                break
        elif 0x80 <= control <= 0x8F:
            cursor_temp += 2
        elif 0x90 <= control <= 0x9F:
            if cursor_temp + 1 < len(rle_data):
                attr = rle_data[cursor_temp+1]
                line_attributes.append(attr)
                cursor_temp += 2
            else:
                break
        else:
            cursor_temp += 1

    # Show output as lines (horizontal) with color
    lines = []
    for line_idx in range(min(5, len(output_chars) // 80 + 1)):
        start = line_idx * 80
        end = min(start + 80, len(output_chars))
        if start < len(output_chars):
            line_bytes = output_chars[start:end]
            line_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line_bytes)
            lines.append(line_str)

            # Apply color if we have attribute for this line
            if line_idx < len(line_attributes):
                attr = line_attributes[line_idx]
                color = vga_to_ansi(attr)
                print(f"Line {line_idx}: {color}{line_str}{RESET}")
            else:
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

        # Display each column with color (use first line's attribute)
        default_color = vga_to_ansi(line_attributes[0]) if line_attributes else ''
        for idx, tline in enumerate(transposed_lines):
            if tline.strip():  # Only print non-empty for readability
                print(f"Col {idx:2d}: '{default_color}{tline}{RESET}'")
            else:
                print(f"Col {idx:2d}: [space]")

        print()
        print("=" * 80)
        print("FINAL READABLE TEXT (all columns concatenated, preserving ALL spaces):")
        print("=" * 80)
        print()

        # Join columns directly - this includes all-space columns too
        readable_text = ''.join(transposed_lines)
        print(f"'{default_color}{readable_text}{RESET}'")

    print()

    # Check if there's leftover data after RLE decoding
    print("=" * 80)
    print("RLE DECODING ANALYSIS:")
    print("=" * 80)
    print()
    print(f"RLE data total size: {len(rle_data)} bytes")
    print(f"Bytes consumed by decoder: {cursor} bytes")
    print(f"Leftover bytes: {len(rle_data) - cursor} bytes")

    if cursor < len(rle_data):
        print()
        print("LEFTOVER DATA (not decoded):")
        leftover = rle_data[cursor:]
        hex_str = ' '.join(f'{b:02x}' for b in leftover)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in leftover)
        print(f"  Hex: {hex_str}")
        print(f"  ASCII: '{ascii_str}'")
    else:
        print()
        print("All RLE data was consumed - no leftover bytes!")

    print()
    print("=" * 80)
    print("FULL PACKET ACCOUNTING:")
    print("=" * 80)
    print(f"  Header:      {len(header_data):3d} bytes (offsets 0-{len(header_data)-1})")
    print(f"  RLE Marker:    4 bytes (offsets {marker_pos}-{marker_pos+3})")
    print(f"  RLE Data:     {len(rle_data):3d} bytes (offsets {marker_pos+4}-{marker_pos+4+len(rle_data)-1})")
    print(f"  TOTAL:       {len(packet):3d} bytes")
    print(f"  Accounted:   {len(header_data) + 4 + len(rle_data):3d} bytes")

    if len(packet) != len(header_data) + 4 + len(rle_data):
        missing = len(packet) - (len(header_data) + 4 + len(rle_data))
        print(f"  MISSING:      {missing:3d} bytes - THERE IS EXTRA DATA!")

        # Show the extra data
        extra_start = marker_pos + 4 + len(rle_data)
        if extra_start < len(packet):
            extra_data = packet[extra_start:]
            print()
            print(f"EXTRA DATA at end (starting at offset {extra_start}):")
            for i in range(0, len(extra_data), 16):
                chunk = extra_data[i:i+16]
                hex_str = ' '.join(f'{b:02x}' for b in chunk)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                print(f"  [{extra_start+i:4d}]: {hex_str:<48} {ascii_str}")
    else:
        print(f"  All bytes accounted for!")

    print()
    break
