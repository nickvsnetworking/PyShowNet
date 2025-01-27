from serial import Serial
ser = Serial("/dev/ttyUSB0", 9600)
import tkinter as tk

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


# hex_list = ['52', '46', '4E' '55', '52', '57', '5A']    #1 through 5 at 10 enter
# #Send the hex values
# ser.write(bytearray.fromhex(''.join(hex_list)))

# hex_list_2 = [commands['1'], commands['THRU'], commands['5'], commands['AT'], commands['5'], commands['0'], commands['ENTER']]
# ser.write(bytearray.fromhex(''.join(hex_list_2)))

# hex_list_3 = [commands['CUE'], commands['0'], commands['GO']]
# ser.write(bytearray.fromhex(''.join(hex_list_3)))

import tkinter as tk

# Command mappings
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

# Function to create the GUI
def create_gui():
    # Create main window
    root = tk.Tk()
    root.title("Command GUI")

    # Terminal display
    terminal_display = tk.Text(root, height=5, width=50, state="disabled", bg="black", fg="white", font=("Courier", 12))
    terminal_display.grid(row=0, column=0, columnspan=5, pady=10)

    # Function to update the terminal
    def update_terminal(command):
        terminal_display.config(state="normal")
        terminal_display.insert(tk.END, f"{command} ")
        terminal_display.config(state="disabled")

    # Function to clear the terminal
    def clear_terminal():
        terminal_display.config(state="normal")
        terminal_display.delete(1.0, tk.END)
        terminal_display.config(state="disabled")

    # Function to handle button press
    def on_button_click(command):
        if command == "ENTER":
            print("Commands executed:", terminal_display.get(1.0, tk.END).strip())
            ser.write(bytearray.fromhex("".join([commands.get(c, "") for c in terminal_display.get(1.0, tk.END).strip().split()])))
            clear_terminal()
        elif command == "BACKSPACE":
            terminal_display.config(state="normal")
            current_text = terminal_display.get(1.0, tk.END).strip().split()
            if current_text:
                terminal_display.delete(1.0, tk.END)
                terminal_display.insert(tk.END, " ".join(current_text[:-1]) + " ")
            terminal_display.config(state="disabled")
        else:
            update_terminal(command)

    # Create buttons for each command
    row, col = 1, 0
    for command in commands.keys():
        btn = tk.Button(root, text=command, width=10, command=lambda cmd=command: on_button_click(cmd))
        btn.grid(row=row, column=col, padx=5, pady=5)
        col += 1
        if col > 4:  # Wrap to the next row after 5 buttons
            col = 0
            row += 1

    # Add a backspace button
    backspace_btn = tk.Button(root, text="BACKSPACE", width=10, command=lambda: on_button_click("BACKSPACE"))
    backspace_btn.grid(row=row + 1, column=0, padx=5, pady=5)

    # Add an enter button
    enter_btn = tk.Button(root, text="ENTER", width=10, command=lambda: on_button_click("ENTER"))
    enter_btn.grid(row=row + 1, column=1, padx=5, pady=5)

    # Start the Tkinter event loop
    root.mainloop()

# Run the GUI
create_gui()
