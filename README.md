# HeyMac

I don't have a great naming scheme yet, so right now HeyMac is two things.
HeyMac is this project where I'm doing a bunch of experimental coding
for wireless data transfer.  HeyMac also happens to be the name I gave
the Medium Access Control, or MAC layer.

HeyMac is a TDMA-style Data Link Layer (Layer 2) designed for use with
low data rate radio modems such as a LoRa radio module on a Raspberry Pi 3.
HeyMac includes a Physical Layer (Layer 1) LoRa radio driver
copied from the [lora_driver](https://github.com/dwhall/lora_driver) project.

HeyMac is written in Python3 using the [farc](https://github.com/dwhall/farc)
hierarchical state machine framework.
You may read about the [HeyMac protocol details here](HeyMacProtocol.md).
HeyMac requires the asyncio module found in Python 3.4 and later.

I am a licensed amateur radio operator in the USA.  So I am using frequencies,
modulations and antenna gains that are not allowed by unlicensed individuals
or persons in other nations.  Know your local regulations before duplicating
these experiments.

## Hardware

During the prototyping stage of development, I'm using a Raspberry Pi 3 Model B.
The radio board is a
[Dragino LoRa/GPS Hat](http://wiki.dragino.com/index.php?title=Lora/GPS_HAT)
that I bought [here](https://www.tindie.com/products/edwin/loragps-hat/).
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

| Device | Signal   | pin |     | pin | Pi signal | Mod |
| ------ | -------- | --- | --- | --- | --------- | --- |
| LoRa   | SPI MISO | 10  |     | 21  | SPI0 MISO |     |
| LoRa   | SPI MOSI | 11  |     | 19  | SPI0 MOSI |     |
| LoRa   | SPI SCLK | 12  |     | 23  | SPI0 SCLK |     |
| LoRa   | SPI SS   | 13  |     | 22  | GPIO 25   | 1   |
| LoRa   | SPI SS   | 13  |     | 24  | SPI0 CS0  | W   |
| LoRa   | DIO0     | 6   |     | 7   | GPIO 4    |     |
| LoRa   | DIO1     | 7   |     | 16  | GPIO 23   |     |
| LoRa   | DIO2     | 8   |     | 18  | GPIO 24   |     |
| LoRa   | DIO3     | 3   |     | 31  | GPIO 6    | W   |
| LoRa   | DIO4     | 4   |     | 29  | GPIO 5    | W   |
| LoRa   | DIO5     | 15  |     | 15  | GPIO 22   | W   |
| LoRa   | RESET    | 14  |     | 11  | GPIO 17   |     |
| GPS    | RX       | 1   |     | 8   | UART TX   |     |
| GPS    | TX       | 2   |     | 10  | UART RX   |     |
| GPS    | PPS      | 6   |     | 37  | GPIO 26   | W   |

| Mod    | Explanation                              |
| ------ | ---------------------------------------- |
| W      | Added a fly wire                         |
| 1      | Either GPIO25 always remains an unusable input, or cut trace to Pi's pin22. |
