from serial import Serial
ser = Serial("/dev/ttyUSB0", 9600)

commands = {
    "CUT": "0D",
    "GO": "20",
    "RECONOSUBS": "31",
    "RECORD": "32",
    "RECTIME": "33",
    "STOP_BACK": "34",
    "DISPLAY": "36",
    "F1": "37",
    "F2": "38",
    "F3": "39",
    "ATCOL": "41",
    "TIME": "42",
    "NEXT": "43",
    "LAST": "44",
    "ON": "45",
    "THRU": "46",
    "FX": "47",
    "7": "48",
    "8": "49",
    "9": "4A",
    "PLUS": "4B",
    "SUB": "4C",
    "4": "4D",
    "5": "4E",
    "6": "4F",
    "MINUS": "50",
    "CUE": "51",
    "1": "52",
    "2": "53",
    "3": "54",
    "AT": "55",
    "MACRO": "56",
    "0": "57",
    ".": "58",
    "CLR": "59",
    "ENTER": "5A",
}


#hex_list = ['52', '46', '4E' '55', '52', '57', '5A']    #1 through 5 at 10 enter
# #Send the hex values
#ser.write(bytearray.fromhex(''.join(hex_list)))

hex_list_2 = [commands['1'], commands['THRU'], commands['5'], commands['AT'], commands['5'], commands['0'], commands['ENTER']]
ser.write(bytearray.fromhex(''.join(hex_list_2)))
#send a CR
ser.write(bytearray.fromhex('0D'))

#hex_list_3 = [commands['GO'], commands['ENTER']]
#ser.write(bytearray.fromhex(''.join(hex_list_3)))
#ser.write(bytearray.fromhex(''.join(hex_list_3)))