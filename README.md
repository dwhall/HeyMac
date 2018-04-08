# HeyMac

I don't have a great naming scheme yet, so right now HeyMac is two things.
HeyMac is this git repo where I'm doing a bunch of experimental coding
on a data radio project.  HeyMac also happens to be the name I gave
the Data Link Layer (Layer 2) a.k.a. the MAC layer.

HeyMac is a TDMA-style Data Link Layer (Layer 2) designed for use with
low data rate radio modems such as a LoRa radio module on a Raspberry Pi 3.
HeyMac builds on top of [lora_driver](https://github.com/dwhall/lora_driver)
the Physical Layer (Layer 1) LoRa radio driver. 
HeyMac is written in Python3 using the [pq](https://github.com/dwhall/pq) 
hierarchical state machine framework.
You may read about the [HeyMac protocol details here](HeyMacProtocol.md).

I am a licensed amateur radio operator in the USA.  So I am using frequencies,
modulations and antenna gains that are not allowed by unlicensed individuals 
or persons in other nations.  Know your local regulations before duplicating
these experiments.

## Hardware

During the prototyping stage of development, I'm using a Raspberry Pi 3 Model B.
The radio board is a Dragino LoRa/GPS Hat that I bought
[here](https://www.tindie.com/products/edwin/loragps-hat/).
They sent me v 1.3 (there are later versions) of the PCB and I had to make 
a few simple mods.  The first and most important fix is to connect the radio's
SPI Chip Select (CS) signal to the Pi's SPI0 CS0.  Without that, you'd have to
programmatically control the radio's CS before and after every transaction
(that's a PITA that slows hardware and software).  It's better to connect the
Pi's CS so the Pi's SPI peripheral can control the CS signal automatically.
The other mods are straight connections from the radio's DIOn pins to the Pi's
GPIO and the GPS's Pulse Per Second (PPS) signal to  the Pi.

Below is a table of the connections between the Raspberry Pi, the
LoRa radio and the GPS.  The "fix" column indicates where I needed to solder
a wire to make the connection.  If the fix column is empty that means the
connection is made by a trace in the Dragino PCB.

| Device | Signal   | pin | | pin | Pi signal | fix |
| ------ | -------- | --- | | --- | --------- | --- |
| LoRa   | SPI MISO | 10  | | 21  | SPI0 MISO |     |
| LoRa   | SPI MOSI | 11  | | 19  | SPI0 MOSI |     |
| LoRa   | SPI SCLK | 12  | | 23  | SPI0 SCLK |     |
| LoRa   | SPI SS   | 13  | | 22  | GPIO 25   | 1   |
| LoRa   | SPI SS   | 13  | | 24  | SPI0 CS0  | W   |
| LoRa   | DIO0     | 6   | | 7   | GPIO 4    |     |
| LoRa   | DIO1     | 7   | | 16  | GPIO 23   |     |
| LoRa   | DIO2     | 8   | | 18  | GPIO 24   |     |
| LoRa   | DIO3     | 3   | | 31  | GPIO 6    | W   |
| LoRa   | DIO4     | 4   | | 29  | GPIO 5    | W   |
| LoRa   | DIO5     | 15  | | 15  | GPIO 22   | W   |
| LoRa   | RESET    | 14  | | 11  | GPIO 17   |     |
| GPS    | RX       | 1   | | 8   | UART TX   |     |
| GPS    | TX       | 2   | | 10  | UART RX   |     |
| GPS    | PPS      | 6   | | 37  | GPIO 26   | W   |

| Fix    | Explanation                              |
| ------ | ---------------------------------------- |
| W      | Added a fly wire                         |
| 1      | Either GPIO25 always remains an unusable input, or cut trace to Pi's pin22. |
