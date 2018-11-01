from . import phy_sx127x_cfg

# Transmit and receive center frequencies
tx_freq = 432.550e6
rx_freq = 432.550e6

# Transmit Margin:
# A transmit begins this amount of time after the beginning of a Tslot
# to allow other nodes time to enable their receiver
tx_margin = 0.005 # secs

# Modem configuration
sx127x_cfg = phy_sx127x_cfg.SX127xConfig(
    bandwidth=250000,
    code_rate="4/6",
    implct_hdr_mode=False,
    spread_factor=128,
    tx_cont=False,
    en_crc=True,
    symbol_count=255, # rx timeout about 1 full frame size
    preamble_len=8, # chip adds 4 more symbol lengths to this
    en_ldr=False,
    agc_auto=True,
    sync_word=0x12)

# RaspberryPi UART (to GPS) configuration.
uart_port = "/dev/serial0"
uart_baud = 9600

# RaspberryPi GPIO configuration.
# This configuration is for the Dragino LoRa GPS Hat v1.3
# with extra connections for DIO3-5 made by the author
reset = {"pin":17, "sig_name":"GPS_RST"}
dio0 = {"pin":4, "sig_name":"PHY_DIO0"}
dio1 = {"pin":23, "sig_name":"PHY_DIO1"}
dio2 = {"pin":24, "sig_name":"PHY_DIO2"}
dio3 = {"pin":6, "sig_name":"PHY_DIO3"}
dio4 = {"pin":5, "sig_name":"PHY_DIO4"}
dio5 = {"pin":22, "sig_name":"PHY_DIO5"}
pps = {"pin":26, "sig_name":"PHY_GPS_PPS"}
