"""
Copyright 2020 Dean Hall.  See LICENSE for details.

Physical layer configuration for SX127xPhy.

Configuration items are things that are hard-wired or
would otherwise require a software reset if they were to change.
"""
# SPI bus (spi_port, spi_cs, spi_freq)
spi_cfg = (0, 0, 10_000_000)

# RPi (BCM GPIO) numbers connected to LoRa DIO0..5
dio_cfg = (4, 23, 24, 6, 5, 22)

# RPi (BCM GPIO) number connected to LoRa RESET
reset_cfg = (17) 
