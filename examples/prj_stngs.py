from sx127x_ahsm import phy_sx127x_stngs


spi_stngs = (0, 0, 20000000)  # Port, CS, MaxClock

modem_stngs = phy_sx127x_stngs.SX127xModemSettings(
    {
    "modulation": "lora",
    "lf_mode": True,
    "modulation_stngs": phy_sx127x_stngs.SX127xLoraSettings(
        # These settings result in approx. 9115 bps
        {
        "op_mode": "stdby",
        "bandwidth": 250000,
        "code_rate": "4/6",
        "implct_hdr_mode": False,
        "spread_factor": 128,
        "tx_cont": False,
        "en_crc": True,
        "symbol_count": 255, # rx timeout about 1 full frame size
        "preamble_len": 8, # chip adds 4 more symbol lengths to this
        "en_ldr": False,
        "agc_auto": True,
        "sync_word": 0x12,
        "tx_base_ptr": 0x00,
        "rx_base_ptr": 0x00,
        })
    })
