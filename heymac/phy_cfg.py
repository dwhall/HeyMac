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
