from serial import Serial
import tkinter as tk

# Initialize the serial connection
ser = Serial("/dev/ttyUSB0", 9600)

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
    "+": "4B",
    "SUB": "4C",
    "4": "4D",
    "5": "4E",
    "6": "4F",
    "MINUS": "50",
    "-": "50",
    "CUE": "51",
    "1": "52",
    "2": "53",
    "3": "54",
    "AT": "55",
    "@": "55",
    "MACRO": "56",
    "0": "57",
    ".": "58",
    "CLR": "59",
    "ENTER": "5A",
    "*": "5A",
}

# Primary button grid layout
primary_layout = [
    ["DIMMER", "LAST", "NEXT", "ON", "THRU", "UNDO"],
    ["FX", "7", "8", "9", "-", "USER"],
    ["SUB", "4", "5", "6", "+", "REM DIM"],
    ["GROUP", "1", "2", "3", "@", "@ATT"],
    ["CUE", "CLR", "0", ".", "*", None]
]

# Function to create the GUI
def create_gui():
    # Initialize the main window
    root = tk.Tk()
    root.title("Serial Command GUI")
    root.geometry("1000x600")

    # Terminal display
    terminal_display = tk.Text(root, height=5, width=80, state="disabled", bg="black", fg="white", font=("Courier", 12))
    terminal_display.pack(pady=10)

    # Function to update the terminal and send the command
    def send_command(command):
        if command in commands:
            hex_value = commands[command]
            ser.write(bytearray.fromhex(hex_value))
            print(f"Sent command: {command} (Hex: {hex_value})")
        else:
            print(f"Unknown command: {command}")
        # Update terminal
        terminal_display.config(state="normal")
        terminal_display.insert(tk.END, f"{command} ")
        terminal_display.config(state="disabled")

    # Function to clear the terminal
    def clear_terminal():
        terminal_display.config(state="normal")
        terminal_display.delete(1.0, tk.END)
        terminal_display.config(state="disabled")

    # Function to handle button presses
    def on_button_click(command):
        print(f"Button clicked: {command}")
        if command == "CLR":  # Backspace functionality
            terminal_display.config(state="normal")
            current_text = terminal_display.get(1.0, tk.END).strip().split()
            if current_text:
                terminal_display.delete(1.0, tk.END)
                terminal_display.insert(tk.END, " ".join(current_text[:-1]) + " ")
            terminal_display.config(state="disabled")
            #send CLR command
            send_command("CLR")
        else:
            send_command(command)

        if command == "*":  # Enter functionality
            send_command("ENTER")
            #send a bunch of Clears
            for i in range(10):
                send_command("CLR")
            clear_terminal()

    # Frame for the primary layout
    primary_frame = tk.Frame(root)
    primary_frame.pack(side="right", padx=20)

    # Create the primary button grid
    for r, row in enumerate(primary_layout):
        for c, command in enumerate(row):
            if command:
                label = "AT" if command == "@" else command  # Map "@" to "AT"
                btn = tk.Button(primary_frame, text=label, width=10, height=2,
                                command=lambda cmd=command: on_button_click(cmd))
                btn.grid(row=r, column=c, padx=5, pady=5)

    # Frame for other buttons
    other_frame = tk.Frame(root)
    other_frame.pack(side="left", padx=20)

    # Add buttons for all other commands
    row, col = 0, 0
    for command in commands.keys():
        if command not in [cmd for row in primary_layout for cmd in row if cmd]:
            btn = tk.Button(other_frame, text=command, width=10, height=2,
                            command=lambda cmd=command: on_button_click(cmd))
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col > 4:  # Wrap to the next row after 5 buttons
                col = 0
                row += 1

    # Start the GUI
    root.mainloop()

# Run the application
create_gui()
