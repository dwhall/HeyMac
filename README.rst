HeyMac
======

HeyMac is a combination of a `frame definition <docs/HeyMacFrame.md>`_,
protocol and and data communication stack
designed to carry Data Link (Layer 2) and Network (Layer 3) frames
between modest data rate, small payload radio modems such as the Semtech SX127x.

HeyMac is written in Python 3 using the `farc <https://github.com/dwhall/farc>`_
state machine framework and is intended to run on a Raspberry Pi 3
running Linux.  HeyMac requires Python 3.5 or later.

I am a licensed amateur radio operator in the USA.  So I am using frequencies,
modulations and antenna gains that are not allowed by unlicensed individuals
or persons in other nations.  Know your local regulations before duplicating
these experiments.


Hardware
--------

During the prototyping stage of development, I'm using a Raspberry Pi 3 Model B.
The radio board is a
`Dragino LoRa/GPS Hat <http://wiki.dragino.com/index.php?title=Lora/GPS_HAT>`_
that I bought `here <https://www.tindie.com/products/edwin/loragps-hat/>`_.
They sent me version 1.3 of the PCB eventhough there are later versions.
So I had to make a couple fixes and a few additions.  The first and most
important fix is to connect the radio's SPI Chip Select (CS) signal to the Pi's
SPI0 CS0.  Without that, you have to programmatically control the radio's CS
before and after every transaction (that's a PITA that slows hardware and
software).  It's better to connect the Pi's CS so the Pi's SPI peripheral
(hardware) can control the CS signal automatically. The additions are direct
connections from the radio's DIOn pins to the Pi's GPIO and the GPS's Pulse Per
Second (PPS) signal to the Pi.

Below is a table of the connections between the Raspberry Pi, the
LoRa radio and the GPS.  The "Mod" column indicates where I needed to solder
a wire to make the connection.  If the Mod column is empty that means the
connection is made by a trace in the Dragino PCB.

======  =========   === ===     === =========   ===
Device  Signal      pin         pin Pi signal   Mod
======  =========   === ===     === =========   ===
LoRa     SPI MISO   10          21  SPI0 MISO
LoRa     SPI MOSI   11          19  SPI0 MOSI
LoRa     SPI SCLK   12          23  SPI0 SCLK
LoRa     SPI SS     13          22  GPIO 25     1
LoRa     SPI SS     13          24  SPI0 CS0    W
LoRa     DIO0       6           7   GPIO 4
LoRa     DIO1       7           16  GPIO 23
LoRa     DIO2       8           18  GPIO 24
LoRa     DIO3       3           31  GPIO 6      W
LoRa     DIO4       4           29  GPIO 5      W
LoRa     DIO5       15          15  GPIO 22     W
LoRa     RESET      14          11  GPIO 17
GPS      RX         1           8   UART TX
GPS      TX         2           10  UART RX
GPS      PPS        6           37  GPIO 26     W
======  =========   === ===     === =========   ===

======  ==========================================
Mod     Explanation
======  ==========================================
W       Added a fly wire
1       Either GPIO25 always remains an unusable
        input, or cut trace to Pi's pin22.
======  ==========================================


Getting Started
---------------

This project is meant to be run on a Raspberry Pi with a LoRa shield.
However, it can also be run in a limited fashion on a PC (posix or windows)
where some of the hardware peripherals are mocked.

The following steps will get you going on a PC or a Pi:

1. Use git to clone this project and its submodules.
2. Use Python's pip tool to install dependencies (see requirements.txt).
3. Run scripts/heymac_gen_creds.py via CLI and answer its questions to generate local credential files.
4. Run example/tui_main.py from the command line for a Text UI.
