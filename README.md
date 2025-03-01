# PyShowNet

Python Strand Shownet to ArtNet converter.

This listens for Strand Shownet (Used in the Strand 300 and 500 series console of the 1990s) and converts it to ArtNet.

These consoles were capable of outputting up to 8192 channels, but in the case of the Strand 520i, only had 4 DMX ports (2048 channels).

This software allows you to use the Networker application to use all 8192 channels over a network on Artnet using the great [StupidArtnet](https://github.com/cpvalente/stupidArtnet) library.

The encoding is super weird, and this was just a hobby project / challenge. I probably wouldn't recommend using a 30 year old lighting console to run shows, nor use this software to output Artnet!

Shownet sends to the broadcast address of the network on UDP port 2501.

Strand built support for "Remote Video" to view the screen of the console from other parts of the venue, using gear like the SN100 Network Node Model 65100. Alas I don't have one of these to be able to sniff / reverse engineer the protocol, it looks like it's running on port 2500, but I haven't done much digging on this.

There's also `serialremote.py` which is a small tkinter application to act as a riggers remote / remote control using the console's Serial Port.