#!/usr/bin/env python3
"""
Copyright 2020 Dean Hall.  See LICENSE for details.
"""

import collections
import time

try:
    import spidev
except:
    from . import mock_spidev as spidev
try:
    import RPi.GPIO as GPIO
except:
    from . import mock_gpio as GPIO

from . import phy_cfg


class PhySX127x(object):
    """Physical (PHY) Layer
    SPI operations, settings management and GPIO interfaces
    for the Semtec SX127x family of digital radio modems.
    """

    # SX127X Oscillator frequency
    SX127X_OSC_FREQ = 32e6 # Hz

    # SPI clock frequency
    SPI_FREQ_MIN =   100000 # arbitrary (slowish)
    SPI_FREQ_MAX = 20000000

    # SX127x DIOs (DO NOT CHANGE VALUES)
    # This table is dual maintenance with  mac_sx127x_ahsm.PhySX127xAhsm._dio_sig_lut
    DIO_MODE_RDY = 0
    DIO_CAD_DETECTED = 1
    DIO_CAD_DONE = 2
    DIO_FHSS_CHG_CHNL = 3
    DIO_RX_TMOUT = 4
    DIO_RX_DONE = 5
    DIO_CLK_OUT = 6
    DIO_PLL_LOCK = 7
    DIO_VALID_HDR = 8
    DIO_TX_DONE = 9
    DIO_PAYLD_CRC_ERR = 10

    # SX127x Radio register addresses
    REG_RDO_FIFO = 0x00
    REG_RDO_OPMODE = 0x01
    REG_RDO_FREQ_MSB = 0x06
    REG_RDO_PA_CFG = 0x09
    REG_RDO_LNA = 0x0C
    REG_RDO_DIOMAP1 = 0x40
    REG_RDO_DIOMAP2 = 0x41
    REG_RDO_CHIP_VRSN = 0x42

    # SX127x LoRa register addresses
    REG_LORA_FIFO_ADDR_PTR = 0x0D
    REG_LORA_FIFO_TX_BASE = 0x0E
    REG_LORA_FIFO_RX_BASE = 0x0F
    REG_LORA_FIFO_CURR_ADDR = 0x10
    REG_LORA_IRQ_MASK = 0x11
    REG_LORA_IRQ_FLAGS = 0x12
    REG_LORA_RX_CNT = 0x13
    REG_LORA_RX_HDR_CNT = 0x14 # MSB first. [2]
    REG_LORA_RX_HDR_CNT_LSB = 0x15
    REG_LORA_RX_PKT_CNT = 0x16 # MSB first. [2]
    REG_LORA_RX_PKT_CNT_LSB = 0x17
    REG_LORA_MODEM_STAT = 0x18
    REG_LORA_PKT_SNR = 0x19
    REG_LORA_PKT_RSSI = 0x1A
    REG_LORA_HOP_CHNL = 0x1C
    REG_LORA_CFG1 = 0x1D
    REG_LORA_CFG2 = 0x1E
    REG_LORA_RX_SYM_TMOUT = 0x1F
    REG_LORA_PREAMBLE_LEN = 0x20
    REG_LORA_PREAMBLE_LEN_LSB = 0x21
    REG_LORA_CFG3 = 0x26
    REG_LORA_RSSI_WB = 0x2C
    REG_LORA_IF_FREQ_2 = 0x2F
    REG_LORA_DTCT_OPTMZ = 0x31
    REG_LORA_SYNC_WORD = 0x39

    # REG_LORA_IRQ_FLAGS bit definitions
    IRQ_FLAGS_RXTIMEOUT           = 0x80
    IRQ_FLAGS_RXDONE              = 0x40
    IRQ_FLAGS_PAYLDCRCERROR       = 0x20
    IRQ_FLAGS_VALIDHEADER         = 0x10
    IRQ_FLAGS_TXDONE              = 0x08
    IRQ_FLAGS_CADDONE             = 0x04
    IRQ_FLAGS_FHSSCHANGEDCHANNEL  = 0x02
    IRQ_FLAGS_CADDETECTED         = 0x01
    IRQ_FLAGS_ALL                 = 0xFF

    # Radio Frequency limits [Hz]
    STNG_RF_FREQ_MIN =  137000000
    STNG_RF_FREQ_MAX = 1020000000

    # LoRa Bandwidth options
    # TX and RX stations must use the same setting.
    STNG_LORA_BW_7K8 = 0    # better sensitivity
    STNG_LORA_BW_10K4 = 1   #
    STNG_LORA_BW_15K6 = 2   #
    STNG_LORA_BW_20K8 = 3   #
    STNG_LORA_BW_31K25 = 4  #
    STNG_LORA_BW_41K7 = 5   #
    STNG_LORA_BW_62K5 = 6   #
    STNG_LORA_BW_125K = 7   #
    STNG_LORA_BW_250K = 8   #
    STNG_LORA_BW_500K = 9   # higher datarate
    STNG_LORA_BW_MIN = 0
    STNG_LORA_BW_MAX = 9

    # LoRa Coding Rate options
    # Included in the PHY's explicit header
    # so robustness can be modified on the fly.
    STNG_LORA_CR_4TO5 = 1   # higher datarate
    STNG_LORA_CR_4TO6 = 2   #
    STNG_LORA_CR_4TO7 = 3   #
    STNG_LORA_CR_4TO8 = 4   # better immunity to noise/interference
    STNG_LORA_CR_MIN = 1
    STNG_LORA_CR_MAX = 4

    # LoRa Spreading Factor options
    # TX and RX stations must use the same setting.
    # Different SF values are orthogonal and may safely occupy the same bands
    STNG_LORA_SF_64_CPS = 6     # higher datarate
    STNG_LORA_SF_128_CPS = 7    #
    STNG_LORA_SF_256_CPS = 8    #
    STNG_LORA_SF_512_CPS = 9    #
    STNG_LORA_SF_1024_CPS = 10  #
    STNG_LORA_SF_2048_CPS = 11  #
    STNG_LORA_SF_4096_CPS = 12  # better sensitivity == increased range
    STNG_LORA_SF_MIN = 6
    STNG_LORA_SF_MAX = 12

    # LoRa Modem Operation Mode
    OPMODE_SLEEP = 0
    OPMODE_STBY = 1
    OPMODE_FSTX = 2
    OPMODE_TX = 3
    OPMODE_FSRX = 4
    OPMODE_RXCONT = 5
    OPMODE_RXONCE = 6
    OPMODE_CAD = 7

    # Field info named tuple
    FldInfo = collections.namedtuple("FldInfo",  "lora_mode reg_start reg_cnt bit_start bit_cnt val_min val_max val_reset")

    # Field info table
    _fld_info = {
        # field                              lora    reg                     reg     bit     bit     val                 val                 val
        # name                               mode    start                   cnt     start   cnt     min                 max                 reset
        "FLD_RDO_LF_MODE":          FldInfo( False,  REG_RDO_OPMODE,         1,      3,      1,      0,                  1,                  1                   ),
        "FLD_RDO_LORA_MODE":        FldInfo( False,  REG_RDO_OPMODE,         1,      7,      1,      0,                  1,                  0                   ),
        "FLD_RDO_FREQ":             FldInfo( False,  REG_RDO_FREQ_MSB,       3,      0,      8,      STNG_RF_FREQ_MIN,   STNG_RF_FREQ_MAX,   0x6C                ),
        "FLD_RDO_OUT_PWR":          FldInfo( False,  REG_RDO_PA_CFG,         1,      0,      4,      0,                  15,                 0x0F                ),
        "FLD_RDO_MAX_PWR":          FldInfo( False,  REG_RDO_PA_CFG,         1,      4,      3,      0,                  7,                  0x04                ),
        "FLD_RDO_PA_BOOST":         FldInfo( False,  REG_RDO_PA_CFG,         1,      7,      1,      0,                  1,                  0                   ),
        "FLD_RDO_LNA_BOOST_HF":     FldInfo( False,  REG_RDO_LNA,            1,      0,      2,      0,                  3,                  0                   ),
        "FLD_RDO_LNA_GAIN":         FldInfo( False,  REG_RDO_LNA,            1,      5,      3,      1,                  6,                  0x01                ),
        "FLD_RDO_DIO0":             FldInfo( False,  REG_RDO_DIOMAP1,        1,      6,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO1":             FldInfo( False,  REG_RDO_DIOMAP1,        1,      4,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO2":             FldInfo( False,  REG_RDO_DIOMAP1,        1,      2,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO3":             FldInfo( False,  REG_RDO_DIOMAP1,        1,      0,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO4":             FldInfo( False,  REG_RDO_DIOMAP2,        1,      6,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO5":             FldInfo( False,  REG_RDO_DIOMAP2,        1,      4,      2,      0,                  2,                  0                   ),

        "FLD_LORA_IMPLCT_HDR_MODE": FldInfo( True,   REG_LORA_CFG1,          1,      0,      1,      0,                  1,                  0                   ),
        "FLD_LORA_CR":              FldInfo( True,   REG_LORA_CFG1,          1,      1,      3,      STNG_LORA_CR_MIN,   STNG_LORA_CR_MAX,   STNG_LORA_CR_4TO5   ),
        "FLD_LORA_BW":              FldInfo( True,   REG_LORA_CFG1,          1,      4,      4,      STNG_LORA_BW_MIN,   STNG_LORA_BW_MAX,   STNG_LORA_BW_125K   ),
        "FLD_LORA_CRC_EN":          FldInfo( True,   REG_LORA_CFG2,          1,      2,      1,      0,                  1,                  0                   ),
        "FLD_LORA_SF":              FldInfo( True,   REG_LORA_CFG2,          1,      4,      4,      STNG_LORA_SF_MIN,   STNG_LORA_SF_MAX,   STNG_LORA_SF_128_CPS),
        "FLD_LORA_RX_TMOUT":        FldInfo( True,   REG_LORA_CFG2,          2,      0,      2,      0,                  (1<<10)-1,          0x00                ),
        "_FLD_LORA_RX_TMOUT_2":     FldInfo( 0,      REG_LORA_RX_SYM_TMOUT,  0,      0,      0,      0,                  0,                  0x64                ),
        "FLD_LORA_PREAMBLE_LEN":    FldInfo( True,   REG_LORA_PREAMBLE_LEN,  2,      0,      16,     0,                  (1<<16)-1,          0x00                ),
        "_FLD_LORA_PREAMBLE_LEN_2": FldInfo( 0,      REG_LORA_PREAMBLE_LEN_LSB, 0,   0,      0,      0,                  0,                  0x08                ),
        "FLD_LORA_AGC_ON":          FldInfo( True,   REG_LORA_CFG3,          1,      2,      1,      0,                  1,                  0                   ),
        "FLD_LORA_SYNC_WORD":       FldInfo( True,   REG_LORA_SYNC_WORD,     1,      0,      8,      0,                  (1<<8)-1,           0x12                ),
    }

    def __init__(self,):
        """Validates the SPI, DIOx pin and Reset pin config.
        Opens the SPI bus with the given port,CS and freq.
        Saves the DIOx pins and Reset pin configs.
        """
        (spi_port, spi_cs, spi_freq) = phy_cfg.spi_cfg
        assert spi_port in (0, 1), "SPI port index must be 0 or 1"
        assert spi_cs in (0, 1), "SPI chip select must be 0 or 1"
        spi_freq = int(spi_freq)
        assert PhySX127x.SPI_FREQ_MIN <= spi_freq <= PhySX127x.SPI_FREQ_MAX, "SPI clock frequency must be within 1-20 MHz"
        self.spi = spidev.SpiDev()
        self.spi.open(spi_port, spi_cs)
        self.spi.max_speed_hz = spi_freq
        self.spi.mode = 0  # phase=0 and polarity=0

        # DIOx: validate and save arguments
        assert len(phy_cfg.dio_cfg) <= 6
        for pin_nmbr in phy_cfg.dio_cfg:
            assert 0 <= pin_nmbr <= 48, "Not a valid RPi GPIO number"
        self.dio_cfg = phy_cfg.dio_cfg

        # Reset: validate and save argument
        assert 0 <= phy_cfg.reset_cfg <= 48, "Not a valid RPi GPIO number"
        self.reset_cfg = phy_cfg.reset_cfg


#### Public methods

    def clear_irq_flags(self,):
        """Writes the IRQ flags reg back to itself to clear the flags
        """
        reg = self._read(SX127xREG_LORA_IRQ_FLAGS)[0]
        self._write(REG_LORA_IRQ_FLAGS, reg)


    def close(self,):
        """Disables GPIO and closes the SPI port.
        """
        # TODO: put the radio in standby or sleep
        GPIO.cleanup()
        self.spi.close()


    def open(self, dio_isr_clbk):
        """Resets the radio, clears internal settings,
        validates the chip communications,
        puts the modem into LoRa mode
        and initializes callbacks for DIOx pin inputs.
        Returns chip comms validity (True/False)
        """
        dio_isr_lut = (self._dio0_isr, self._dio1_isr, self._dio2_isr, self._dio3_isr, self._dio4_isr, self._dio5_isr)
        self._dio_isr_clbk = dio_isr_clbk

        GPIO.setmode(GPIO.BCM)

        self.reset_rdo()

        valid = self._validate_chip()

        # Put the radio in LoRa mode so DIO5 outputs ModeReady (instead of ClkOut)
        # This is needed so the state machine receives the ModeReady event
        self.write_opmode(PhySX127x.OPMODE_SLEEP, False)
        self.set_fld("FLD_RDO_LORA_MODE", 1)
        self.write_sleep_stngs()
        self.write_opmode(PhySX127x.OPMODE_STBY, False)
        self._rdo_stngs_applied["FLD_RDO_LORA_MODE"] = 1

        # Init DIOx pins
        if dio_isr_clbk is not None:
            n = 0
            for pin_nmbr in self.dio_cfg:
                if type(pin_nmbr) is int and pin_nmbr != 0:
                    GPIO.setup(pin_nmbr, GPIO.IN)
                    GPIO.add_event_detect(pin_nmbr, edge=GPIO.RISING, callback=dio_isr_lut[n])
                n += 1

        return valid


    def read_lora_rxd(self,):
        """Returns a tuple of: (payld, rssi, snr)
        payld is a bytearray.
        rssi is an integer [dBm].
        snr is a float [dB].
        """
        # Read the index into the FIFO of where the pkt starts
        # and the length of the data received
        pkt_start, _, _, nbytes = self._read(REG_RX_CURRENT_ADDR, 4)
        assert pkt_start == 0, "rxd pkt_start was not at 0"

        # Read the payload
        self._write(REG_LORA_FIFO_ADDR_PTR, pkt_start)
        payld = self._read(REG_RDO_FIFO, nbytes)

        # Read the packet SNR and RSSI (2 consecutive regs)
        # and calculate RSSI [dBm] and SNR [dB]
        snr, rssi = self._read(REG_LORA_PKT_SNR, 2)
        rssi = -157 + rssi
        snr = snr / 4.0

        return (bytes(payld), rssi, snr)


    def read_opmode(self,):
        """Reads and returns OPMODE from its register
        """
        return 0x07 & self._read(PhySX127x.REG_RDO_OPMODE)[0]


    def reset_rdo(self,):
        """Resets the radio
        and internal tracking of radio settings
        """
        # Init empty settings
        self._rng_raw = 0

        # Init the reset pin and toggle it to reset the SX127x
        GPIO.setup(self.reset_cfg, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.output(self.reset_cfg, GPIO.LOW)
        time.sleep(0.000110)  # >100us
        GPIO.output(self.reset_cfg, GPIO.HIGH)
        time.sleep(0.005) # >5ms

        self._reset_rdo_stngs()


    def set_fld(self, fld, val):
        """Sets the field to the value.
        The field is not written to the register until
        the radio is between TX, RX operations
        """
        assert fld in PhySX127x._fld_info.keys(), "Invalid field name"
        minval = PhySX127x._fld_info[fld].val_min
        maxval = PhySX127x._fld_info[fld].val_max
        assert minval <= val <= maxval, "Invalid value"

        # Settings special cases for multi-reg values
        if fld == "FLD_RDO_FREQ":
            assert PhySX127x._fld_info[fld].reg_cnt == 3
            # Errata 2.3: store freq so rejection offset may be applied during write_stngs()
            self._rdo_stngs_freq = val

        elif fld == "FLD_LORA_RX_TMOUT":
            assert PhySX127x._fld_info[fld].reg_cnt == 2
            self._rdo_stngs["FLD_LORA_RX_TMOUT"] = (val >> 8) & 0xFF
            self._rdo_stngs["_FLD_LORA_RX_TMOUT_2"] = (val >> 0) & 0xFF

        elif fld == "FLD_LORA_PREAMBLE_LEN":
            assert PhySX127x._fld_info[fld].reg_cnt == 2
            self._rdo_stngs["FLD_LORA_PREAMBLE_LEN"] = (val >> 8) & 0xFF
            self._rdo_stngs["_FLD_LORA_PREAMBLE_LEN_2"] = (val >> 0) & 0xFF

        # Settings normal case for single-reg values
        else:
            assert PhySX127x._fld_info[fld].reg_cnt == 1
            self._rdo_stngs[fld] = val & self._bit_fld(0, PhySX127x._fld_info[fld].bit_cnt)


    def stngs_require_sleep(self,):
        """Returns True if any outstanding settings must be applied in sleep mode.
        At this time, only the LoRa Mode requires sleep mode.
        """
        return self._rdo_stngs["FLD_RDO_LORA_MODE"] != self._rdo_stngs_applied["FLD_RDO_LORA_MODE"]


    def updt_rng(self,):
        """The RSSI Wideband register's least significant bit
        provides a noise source for a Random Number Generator
        """
        reg = self._read(PhySX127x.REG_LORA_RSSI_WB)[0]
        self._rng_raw = (self._rng_raw << 1) | (reg & 1)
        # TODO: feed an octet of raw bits into a hash algorithm

    def write_fifo(self, data, sz=None):
        if not bool(sz):
            sz = len(data)
        assert 0 < sz < 256, "Data will not fit in the radio's FIFO"
        self._write(PhySX127x.REG_RDO_FIFO, data[:sz])


    def write_fifo_ptr(self, offset):
        assert 0 <= offset < 256
        self._write(PhySX127x.REG_LORA_FIFO_ADDR_PTR, [offset]*3)


    def write_lora_irq_flags(self, clear_these):
        self._write(PhySX127x.REG_LORA_IRQ_FLAGS, clear_these)


    def write_lora_irq_mask(self, disable_these, enable_these):
        reg = self._read(PhySX127x.REG_LORA_IRQ_MASK)[0]
        reg |= (disable_these & 0xFF)
        reg &= (~enable_these & 0xFF)
        self._write(PhySX127x.REG_LORA_IRQ_MASK, reg)


    def write_opmode(self, opmode, en_mode_rdy=False):
        reg = self._read(PhySX127x.REG_RDO_OPMODE)[0]
        reg &= (~0x7 & 0xFF)
        reg |= (0x7 & opmode)
        self._write(PhySX127x.REG_RDO_OPMODE, reg)
        # Enable/disable DIO5 callback
        self._en_dio5_clbk = en_mode_rdy


    def write_sleep_stngs(self,):
        """Writes settings that need the chip to be in sleep mode.
        At this time, only the LoRa Mode requires sleep mode.
        """
        # If the setting has not changed, skip it
        if self._rdo_stngs["FLD_RDO_LORA_MODE"] != self._rdo_stngs_applied["FLD_RDO_LORA_MODE"]:
            # RMW to LoRa Mode bit in the OpMode reg
            reg = self.read_opmode()
            if self._rdo_stngs["FLD_RDO_LORA_MODE"]:
                reg |= 0x80
            else:
                reg &= 0x7F
            self._write(PhySX127x.REG_RDO_OPMODE, reg)
            # Record what was written
            self._rdo_stngs_applied["FLD_RDO_LORA_MODE"] = self._rdo_stngs["FLD_RDO_LORA_MODE"]


    def write_stng(self, fld):
        """Writes one setting to its register(s)
        """
        assert fld in PhySX127x._fld_info.keys(), "Invalid settings field name"

        if self._rdo_stngs[fld] != self._rdo_stngs_applied[fld]:
            reg = self._read(PhySX127x._fld_info[fld].reg_start)[0]
            bitf = self._bit_fld(PhySX127x._fld_info[fld].bit_start,
                                 PhySX127x._fld_info[fld].bit_cnt)
            reg &= (~bitf & 0xFF)
            reg |= (bitf & ( self._rdo_stngs[fld] << PhySX127x._fld_info[fld].bit_start))
            self._write(PhySX127x._fld_info[fld].reg_start, reg)
            # Record what was written
            self._rdo_stngs_applied[fld] = self._rdo_stngs[fld]


    def write_stngs(self, for_rx):
        """Writes the settings values that are changed
        to the proper radio registers
        """
        freq = self._rdo_stngs_freq
        auto_if_on = False  # Errata-recommended value after reset
        reg_if_freq2 = 0x20  # Reset value

        # Apply Errata 2.3 for LoRa mode receving
        if for_rx and self._rdo_stngs["FLD_RDO_LORA_MODE"]:
            if self._rdo_stngs["FLD_LORA_BW"] >= PhySX127x.STNG_LORA_BW_500K:
                auto_if_on = True
            else:
                # Adjust the intermediate freq per errata
                if_freq2_lut = ( 0x48, 0x44, 0x44, 0x44, 0x44, 0x44, 0x40, 0x40, 0x40, )
                reg_if_freq2 = if_freq2_lut[self._rdo_stngs["FLD_LORA_BW"]]
                # Add the offset to the carrier freq and fill the stngs holding array with that
                refection_offset_hz_lut = ( 7810, 10420, 15620, 20830, 31250, 41670, 0, 0, 0, )
                freq += refection_offset_hz_lut[self._rdo_stngs["FLD_LORA_BW"]]

        # If LoRa mode or LoRa BW has changed, apply the errata values to their regs
        if((self._rdo_stngs["FLD_RDO_LORA_MODE"] != self._rdo_stngs_applied["FLD_RDO_LORA_MODE"]) or
           (self._rdo_stngs["FLD_LORA_BW"] != self._rdo_stngs_applied["FLD_LORA_BW"])):
            self._write(PhySX127x.REG_LORA_IF_FREQ_2, reg_if_freq2)
            reg = self._read(PhySX127x.REG_LORA_DTCT_OPTMZ)[0]
            reg &= 0x7F
            reg |= (0, 0x80)[auto_if_on]
            self._write(PhySX127x.REG_LORA_DTCT_OPTMZ, reg)

        # Write outstanding carrier freq to the regs
        if freq != self._rdo_stngs_freq_applied:
            reg_freq = [
                (freq >> 16) & 0xFF,    # MSB
                (freq >> 8) & 0xFF,     # MID
                (freq >> 0) & 0xFF,     # LSB
            ]
            self._write(PhySX127x.REG_RDO_FREQ_MSB, reg_freq)
            self._rdo_stngs_freq_applied = freq

        # RMW typical settings if they have changed
        for fld in PhySX127x._fld_info.keys():
            self.write_stng(fld)


#### Private methods

    def _bit_fld(self, ls1, nbits):
        """Creates a bitfield per
        https://stackoverflow.com/questions/8774567/c-macro-to-create-a-bit-mask-possible-and-have-i-found-a-gcc-bug
        """
        assert nbits <= 8
        return ((0xFF >> (7 - ((ls1) + (nbits) - 1))) & ~((1 << (ls1)) - 1))


    def _dio0_isr(self, chnl):
        dio0_to_sig_lut = (
            PhySX127x.DIO_RX_DONE,
            PhySX127x.DIO_TX_DONE,
            PhySX127x.DIO_CAD_DONE,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO0"] < len(dio0_to_sig_lut)
        self._dio_isr_clbk(dio0_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO0"]])


    def _dio1_isr(self, chnl):
        dio1_to_sig_lut = (
            PhySX127x.DIO_RX_TMOUT,
            PhySX127x.DIO_FHSS_CHG_CHNL,
            PhySX127x.DIO_CAD_DETECTED,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO1"] < len(dio1_to_sig_lut)
        self._dio_isr_clbk(dio1_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO1"]])


    def _dio2_isr(self, chnl):
        dio2_to_sig_lut = (
            PhySX127x.DIO_FHSS_CHG_CHNL,
            PhySX127x.DIO_FHSS_CHG_CHNL,
            PhySX127x.DIO_FHSS_CHG_CHNL,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO2"] < len(dio2_to_sig_lut)
        self._dio_isr_clbk(dio2_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO2"]])


    def _dio3_isr(self, chnl):
        dio3_to_sig_lut = (
            PhySX127x.DIO_CAD_DONE,
            PhySX127x.DIO_VALID_HDR,
            PhySX127x.DIO_PAYLD_CRC_ERR,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO3"] < len(dio3_to_sig_lut)
        self._dio_isr_clbk(dio3_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO3"]])


    def _dio4_isr(self, chnl):
        dio4_to_sig_lut = (
            PhySX127x.DIO_CAD_DETECTED,
            PhySX127x.DIO_PLL_LOCK,
            PhySX127x.DIO_PLL_LOCK,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO4"] < len(dio4_to_sig_lut)
        self._dio_isr_clbk(dio4_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO4"]])


    def _dio5_isr(self, chnl):
        dio5_to_sig_lut = (
            PhySX127x.DIO_MODE_RDY,
            PhySX127x.DIO_CLK_OUT,
            PhySX127x.DIO_CLK_OUT,
        )
        assert self._rdo_stngs_applied["FLD_RDO_DIO5"] < len(dio5_to_sig_lut)
        if self._en_dio5_clbk:
            self._dio_isr_clbk(dio5_to_sig_lut[self._rdo_stngs_applied["FLD_RDO_DIO5"]])


    def _read(self, reg_addr, nbytes=1):
        """Reads a byte (or more) from the register.
        Returns list of bytes (even if there is only one).
        """
        assert type(nbytes) is int
        assert nbytes > 0
        b = [reg_addr,]
        b.extend([0,] * nbytes)
        return self.spi.xfer2(b)[1:]


    def _reset_rdo_stngs(self,):
        """Sets the internal settings data
        to the radio register reset values.
        This should be done after a chip reset
        so this driver is synchronized with the chip.
        """
        self._rdo_stngs = {}
        self._rdo_stngs_applied = {}
        self._rdo_stngs_freq_applied = 0

        for fld in PhySX127x._fld_info.keys():
            val = PhySX127x._fld_info[fld].val_reset
            self._rdo_stngs[fld] = val
            self._rdo_stngs_applied[fld] = val


    def _validate_chip(self,):
        """Returns True if the SX127x chip and the SPI bus are operating.
        """
        CHIP_VRSN = 0x12
        return CHIP_VRSN == self._read(PhySX127x.REG_RDO_CHIP_VRSN)[0]


    def _write(self, reg_addr, data):
        """Writes one or more bytes to the register.
        Returns list of bytes (even if there is only one).
        """
        assert type(data) == int or isinstance(data, collections.Sequence)

        # Set the write bit (MSb)
        reg_addr |= 0x80

        # Build the list of bytes to write
        if type(data) == int:
            data &= 0xff
            b = [reg_addr, data]
        else:
            b = [reg_addr,]
            b.extend(data)

        return self.spi.xfer2(b)[1:]
