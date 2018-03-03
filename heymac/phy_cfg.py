import lora_driver

# Transmit and receive center frequencies
tx_freq = 432.550e6
rx_freq = 432.550e6

tx_margin = 0.030 # secs

# Modem configuration
sx127x_cfg = lora_driver.SX127xConfig(
    bandwidth=250000,
    code_rate="4/6",
    implct_hdr_mode=False,
    spread_factor=128,
    tx_cont=False,
    en_crc=False,
    symbol_count=255, # rx timeout about 1 full frame size
    preamble_len=8, # chip adds 4 more symbol lengths to this
    en_ldr=False,
    agc_auto=True,
    sync_word=0x12)

# GPIO configuration
reset = {"pin":17, "sig_name":"GPS_RST"}
dio0 = {"pin":4, "sig_name":"PHY_DIO0"}
dio1 = {"pin":23, "sig_name":"PHY_DIO1"}
dio2 = {"pin":24, "sig_name":"PHY_DIO2"}
pps = {"pin":26, "sig_name":"PHY_GPS_PPS"}
