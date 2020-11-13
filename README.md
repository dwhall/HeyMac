# phy_sx127x

A physical layer (PHY) driver for the Semtech SX127x radio data modem
written in Python3 using the [farc](https://github.com/dwhall/farc)
hierarchical state machine framework
and meant to run on Linux on a Raspberry Pi 3
with a modified [Dragino LoRa GPS Hat](https://wiki.dragino.com/index.php?title=Lora/GPS_HAT).

A state machine manages the operational behavior and calls into a PHY layer module
to interact with the radio via the SPI bus and GPIO pins.

This repository is designed to be a git submodule
so that it may be re-used by multiple projects
and is not operational on its own.

## PHY Layer State Machine

phy_sx127x_ahsm.py

## PHY Layer Module

phy_sx127x.py

## Hardware

The prototype platform is a 
[Raspberry Pi 3 Model B](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/?resellerType=home)
with a
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

Below is a table of the connections between the Raspberry Pi and the
LoRa radio.  The "Mod" column indicates where I needed to solder
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

| Mod    | Explanation                              |
| ------ | ---------------------------------------- |
| W      | Added a fly wire                         |
| 1      | Either GPIO25 always remains an unusable input, or cut trace to Pi's pin22. |


# Getting Started

This repository is designed to be a git submodule and is not operational on its own.
