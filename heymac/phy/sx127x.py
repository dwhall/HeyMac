"""
Copyright 2020 Dean Hall.  See LICENSE for details.
"""

import collections
import math
import time

try:
    import spidev
except ImportError:
    from . import mock_spidev as spidev
try:
    import RPi.GPIO as GPIO
except ImportError:
    from . import mock_gpio as GPIO

from .platform_cfg import SpiConfig, DioConfig, ResetConfig


class NoiseAccumulator():
    """Accumulates bits of noise.  Returns noise as a bytearray."""
    MAX_LEN = 256

    _noise = bytearray()
    _byte = 0
    _bit_cnt = 0

    @classmethod
    def append(cls, bit):
        """Accumulates one bit of noise into a byte.
        When the byte is full, append it to a FIFO.
        Cap the FIFO at a max size (tossing oldest bits).
        """
        cls._byte |= (bit << cls._bit_cnt)
        cls._bit_cnt += 1
        if cls._bit_cnt == 8:
            cls._noise.append(cls._byte)
            cls._bit_cnt = 0
            cls._byte = 0
            if len(cls._noise) > NoiseAccumulator.MAX_LEN:
                cls._noise = cls._noise[-NoiseAccumulator.MAX_LEN:]

    @classmethod
    def noise(cls, length=4):
        """Returns a bytearray of the given length (4 default, 256 max),
        if enough noise bytes have accumulated.  Returns None otherwise.
        """
        val = None
        length = min(max(0, length), NoiseAccumulator.MAX_LEN)
        if length <= len(cls._noise):
            val = cls._noise[:length]
            cls._noise = cls._noise[length:]
        return val


class SX127x():
    """The PHY layer SPI operations, settings management and GPIO
    interfaces for the Semtec SX127x family of digital radio transceivers.
    For now, this library only supports LoRa mode.
    """

    # SX127x Oscillator frequency
    SX127X_OSC_FREQ = 32e6  # Hz

    # SX127x DIOs (DO NOT CHANGE VALUES)
    # This table is dual maintenance with
    # sx127x_hsm.SX127xHsm._dio_sig_lut
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
    REG_LORA_RX_HDR_CNT = 0x14      # MSB first. [2]
    REG_LORA_RX_HDR_CNT_LSB = 0x15
    REG_LORA_RX_PKT_CNT = 0x16      # MSB first. [2]
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
    REG_LORA_PAYLD_LEN = 0x22
    REG_LORA_CFG3 = 0x26
    REG_LORA_RSSI_WB = 0x2C
    REG_LORA_IF_FREQ_2 = 0x2F
    REG_LORA_DTCT_OPTMZ = 0x31
    REG_LORA_SYNC_WORD = 0x39

    # REG_LORA_IRQ_FLAGS bit definitions
    IRQ_FLAGS_RXTIMEOUT = 0x80
    IRQ_FLAGS_RXDONE = 0x40
    IRQ_FLAGS_PAYLDCRCERROR = 0x20
    IRQ_FLAGS_VALIDHEADER = 0x10
    IRQ_FLAGS_TXDONE = 0x08
    IRQ_FLAGS_CADDONE = 0x04
    IRQ_FLAGS_FHSSCHANGEDCHANNEL = 0x02
    IRQ_FLAGS_CADDETECTED = 0x01
    IRQ_FLAGS_ALL = 0xFF

    # LoRa Modem Operation Mode
    OPMODE_SLEEP = 0
    OPMODE_STBY = 1
    OPMODE_FSTX = 2
    OPMODE_TX = 3
    OPMODE_FSRX = 4
    OPMODE_RXCONT = 5
    OPMODE_RXONCE = 6
    OPMODE_CAD = 7

    def __init__(self, spi_cfg, dio_cfg, reset_cfg):
        """Saves config info, opens the SPI bus and init a settings object."""
        assert isinstance(spi_cfg, SpiConfig)
        assert isinstance(dio_cfg, DioConfig)
        assert isinstance(reset_cfg, ResetConfig)

        # Save all config objects
        self._spi_cfg = spi_cfg
        self._dio_cfg = dio_cfg
        self._reset_cfg = reset_cfg

        self._stngs = SX127xSettings()

# Public

    @property
    def noise(self, length=4):
        """Returns a bytearray of the given length (4 default, 256 max),
        from the noise accumulator if enough noise bytes have accumulated.
        Returns None otherwise.
        """
        return NoiseAccumulator.noise(length)


    def calc_on_air_time(self, payld_len):
        """Returns the on-air time for the given TX bytes."""
        # Prepare input params
        BW = self._get_actual_bw(self._stngs.get_applied("FLD_LORA_BW"))
        SF = self._stngs.get_applied("FLD_LORA_SF")
        n_pre = 0  # reset
        PL = payld_len
        CRC = self._stngs.get_applied("FLD_LORA_CRC_EN")
        IH = self._stngs.get_applied("FLD_LORA_IMPLCT_HDR_MODE")
        DE = 0  # reset
        CR = self._stngs.get_applied("FLD_LORA_CR")

        # Equations from SX1276 datasheet v6, p31
        inner_term = (2 * PL - SF + 7 + 4 * CRC - 5 * IH) / (SF - 2 * DE)
        n_payld = 8 + max(math.ceil(inner_term) * (CR + 4), 0)
        Tsym = (2 ** SF) / BW
        Tpkt = (4.25 + n_pre + n_payld) * Tsym
        return Tpkt


    def clear_irq_flags(self):
        """Writes the IRQ flags reg back to itself to clear the flags
        """
        reg = self._read(SX127x.REG_LORA_IRQ_FLAGS)[0]
        self._write(SX127x.REG_LORA_IRQ_FLAGS, reg)


    def close(self):
        """Closes the SX127x command interface.
        Puts the radio in Sleep mode, disables GPIO and closes the SPI port.
        """
        self.write_opmode(SX127x.OPMODE_SLEEP)
        GPIO.cleanup()
        self.spi.close()


    def get_applied_stngs(self):
        """Returns the applied settings"""
        return self._stngs.get_applied_stngs()


    def in_sim_mode(self):
        """Returns True if this driver is simulating the radio interface."""
        return "mock" in str(spidev)


    def init_gpio(self):
        """Inits the GPIO pins that connect to LoRa DIO pins"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._reset_cfg.pin, GPIO.OUT, initial=GPIO.HIGH)
        for n, pin_nmbr in enumerate(self._dio_cfg.pins):
            GPIO.setup(pin_nmbr, GPIO.IN)


    def open(self, dio_isr_clbk):
        """Opens the SX127x command interface.

        Opens the SPI port.
        Validates the chip communications,
        puts the modem into LoRa mode
        and initializes callbacks for DIOx pin inputs.
        Returns chip comms validity (True/False)
        """
        # Open the SPI bus
        spi = spidev.SpiDev()
        spi.open(self._spi_cfg.port, self._spi_cfg.cs)
        spi.max_speed_hz = self._spi_cfg.freq
        spi.mode = 0  # phase=0 and polarity=0
        self.spi = spi

        # Validate SPI communication with a SX127x device
        valid = self._validate_chip()

        # Put radio in LoRa mode so DIO5 outputs ModeReady instead of ClkOut
        # This is needed so the state machine receives the ModeReady event
        self.write_opmode(SX127x.OPMODE_SLEEP)
        self.set_fld("FLD_RDO_LORA_MODE", 1)
        self.write_sleep_settings()
        self.write_opmode(SX127x.OPMODE_STBY)
        self._stngs.apply("FLD_RDO_LORA_MODE")

        # Init DIOx pin callbacks
        dio_isr_lut = (
            self._dio0_isr, self._dio1_isr, self._dio2_isr, self._dio3_isr,
            self._dio4_isr, self._dio5_isr)
        self._dio_isr_clbk = dio_isr_clbk
        if dio_isr_clbk is not None:
            for n, pin_nmbr in enumerate(self._dio_cfg.pins):
                GPIO.add_event_detect(
                    pin_nmbr, edge=GPIO.RISING, callback=dio_isr_lut[n])

        return valid


    def read_lora_rxd(self):
        """Returns a tuple of: (payld, rssi, snr, flags)
        payld is a bytearray.
        rssi is an integer [dBm].
        snr is a float [dB].
        flags is 0 if rx is good, otherwise it is bitwise combo of IRQ_FLAGS_*.
        """
        # Clear rx-related IRQ flags in the reg
        reg = self._read(SX127x.REG_LORA_IRQ_FLAGS)[0]
        flags = reg & (
            SX127x.IRQ_FLAGS_RXTIMEOUT
            | SX127x.IRQ_FLAGS_RXDONE
            | SX127x.IRQ_FLAGS_PAYLDCRCERROR
            | SX127x.IRQ_FLAGS_VALIDHEADER)
        self._write(SX127x.REG_LORA_IRQ_FLAGS, flags)

        # Determine rx status from flags
        good_rx = bool(flags & SX127x.IRQ_FLAGS_RXDONE)
        flags &= (SX127x.IRQ_FLAGS_RXTIMEOUT | SX127x.IRQ_FLAGS_PAYLDCRCERROR)
        if flags:
            good_rx = False

        # Read the packet SNR and RSSI (2 consecutive regs)
        # and calculate RSSI [dBm] and SNR [dB]
        snr, rssi = self._read(SX127x.REG_LORA_PKT_SNR, 2)
        rssi = -157 + rssi
        snr = snr / 4.0

        if good_rx:
            # Read the address of where the pkt starts
            # and the length of the data received,
            # then set the pointer and read the packet
            pkt_start, _, _, nbytes = \
                self._read(SX127x.REG_LORA_FIFO_CURR_ADDR, 4)
            self._write(SX127x.REG_LORA_FIFO_ADDR_PTR, pkt_start)
            payld = self._read(SX127x.REG_RDO_FIFO, nbytes)
        else:
            payld = b""

        return (bytes(payld), rssi, snr, flags)


    def read_opmode(self):
        """Reads and returns OPMODE from its register
        """
        return 0x07 & self._read(SX127x.REG_RDO_OPMODE)[0]


    def reset_rdo(self):
        """Resets the radio and internal tracking of radio settings.
        Caller must wait 5ms after calling this to interact with radio SPI.
        """
        # Toggle the reset pin to reset the SX127x
        GPIO.output(self._reset_cfg.pin, GPIO.LOW)
        time.sleep(self._reset_cfg.pin_low_time)
        GPIO.output(self._reset_cfg.pin, GPIO.HIGH)

        self._stngs.reset()


    def set_fld(self, fld, val):
        """Sets the field to the value.
        The field is not written to the register(s) in this procedure.
        Once all the fields have been set, call write_stngs() to write
        all of the settings to the register(s).
        """
        self._stngs.set(fld, val)


    def set_flds(self, stngs):
        """Sets all of the (field, value) pairs in stngs.
        The fields are not written to the register(s) in this procedure.
        Once all the fields have been set, call write_stngs() to write
        all of the settings to the register(s).
        """
        for fld, val in stngs.items():
            self.set_fld(fld, val)


    def stngs_require_sleep(self):
        """Returns True if any outstanding settings require
        being in sleep mode to be applied.
        At this time, only the LoRa Mode requires sleep mode.
        """
        return self._stngs.changed("FLD_RDO_LORA_MODE")


    def updt_noise(self):
        """Accumulates noise from the RSSI Wideband register's lsb.
        Use the .noise property to fetch an arbitrary value
        from this noise source.
        """
        NoiseAccumulator.append(1 & self._read(SX127x.REG_LORA_RSSI_WB)[0])


    def write_fifo(self, data, sz=None):
        if not bool(sz):
            sz = len(data)
        assert 0 < sz < 256, "Data will not fit in the radio's FIFO"
        self._write(SX127x.REG_RDO_FIFO, data[:sz])


    def write_fifo_ptr(self, offset):
        assert 0 <= offset < 256
        self._write(SX127x.REG_LORA_FIFO_ADDR_PTR, [offset] * 3)


    def write_lora_irq_flags(self, clear_these):
        self._write(SX127x.REG_LORA_IRQ_FLAGS, clear_these)


    def write_lora_irq_mask(self, disable_these, enable_these):
        reg = self._read(SX127x.REG_LORA_IRQ_MASK)[0]
        reg |= (disable_these & 0xFF)
        reg &= (~enable_these & 0xFF)
        self._write(SX127x.REG_LORA_IRQ_MASK, reg)


    def write_lora_payld_len(self, payld_len):
        self._write(SX127x.REG_LORA_PAYLD_LEN, payld_len)


    def write_opmode(self, opmode):
        reg = self._read(SX127x.REG_RDO_OPMODE)[0]
        reg &= (~0x7 & 0xFF)
        reg |= (0x7 & opmode)
        self._write(SX127x.REG_RDO_OPMODE, reg)


    def write_sleep_settings(self):
        """Writes settings that need the chip to be in sleep mode.
        At this time, only the LoRa Mode requires sleep mode.
        """
        if self._stngs.changed("FLD_RDO_LORA_MODE"):
            # RMW to LoRa Mode bit in the OpMode reg
            reg = self.read_opmode()
            if self._stngs.get("FLD_RDO_LORA_MODE"):
                reg |= 0x80
            else:
                reg &= 0x7F
            self._write(SX127x.REG_RDO_OPMODE, reg)
            self._stngs.apply("FLD_RDO_LORA_MODE")


    def write_stng(self, fld):
        """Writes one setting to its register(s)"""
        if self._stngs.changed(fld):
            reg = self._read(SX127xSettings.get_reg(fld))[0]
            reg = self._stngs.modify(fld, reg)
            self._write(SX127xSettings.get_reg(fld), reg)
            self._stngs.apply(fld)


    def write_stngs(self, for_rx):
        """Writes changed settings to the registers"""
        assert type(for_rx) is bool

        self._write_errata(for_rx)
        for fld in SX127xSettings.get_field_names():
            self.write_stng(fld)


# Private


    def _dio0_isr(self, chnl):
        dio0_to_sig_lut = (
            SX127x.DIO_RX_DONE,
            SX127x.DIO_TX_DONE,
            SX127x.DIO_CAD_DONE,
        )
        self._dio_isr_clbk(
            dio0_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO0")])


    def _dio1_isr(self, chnl):
        dio1_to_sig_lut = (
            SX127x.DIO_RX_TMOUT,
            SX127x.DIO_FHSS_CHG_CHNL,
            SX127x.DIO_CAD_DETECTED,
        )
        self._dio_isr_clbk(
            dio1_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO1")])


    def _dio2_isr(self, chnl):
        dio2_to_sig_lut = (
            SX127x.DIO_FHSS_CHG_CHNL,
            SX127x.DIO_FHSS_CHG_CHNL,
            SX127x.DIO_FHSS_CHG_CHNL,
        )
        self._dio_isr_clbk(
            dio2_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO2")])


    def _dio3_isr(self, chnl):
        dio3_to_sig_lut = (
            SX127x.DIO_CAD_DONE,
            SX127x.DIO_VALID_HDR,
            SX127x.DIO_PAYLD_CRC_ERR,
        )
        self._dio_isr_clbk(
            dio3_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO3")])


    def _dio4_isr(self, chnl):
        dio4_to_sig_lut = (
            SX127x.DIO_CAD_DETECTED,
            SX127x.DIO_PLL_LOCK,
            SX127x.DIO_PLL_LOCK,
        )
        self._dio_isr_clbk(
            dio4_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO4")])


    def _dio5_isr(self, chnl):
        dio5_to_sig_lut = (
            SX127x.DIO_MODE_RDY,
            SX127x.DIO_CLK_OUT,
            SX127x.DIO_CLK_OUT,
        )
        self._dio_isr_clbk(
            dio5_to_sig_lut[self._stngs.get_applied("FLD_RDO_DIO5")])


    @staticmethod
    def _get_actual_bw(bw_idx):
        actual_bw = (
            7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000,
            500000)
        return actual_bw[bw_idx]

    def _read(self, reg_addr, nbytes=1):
        """Reads a byte (or more) from the register.
        Returns list of bytes (even if there is only one).
        """
        assert type(nbytes) is int
        assert nbytes > 0
        b = [reg_addr]
        b.extend([0] * nbytes)
        return self.spi.xfer2(b)[1:]


    def _validate_chip(self):
        """Returns True if the SX127x chip and the SPI bus are operating.
        """
        CHIP_VRSN = 0x12
        return CHIP_VRSN == self._read(SX127x.REG_RDO_CHIP_VRSN)[0]


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
            b = [reg_addr]
            b.extend(data)

        return self.spi.xfer2(b)[1:]


    def _write_errata(self, for_rx):
        freq = self._stngs.get("FLD_RDO_FREQ")
        auto_if_on = False  # Errata-recommended value after reset
        reg_if_freq2 = 0x20  # Reset value

        # Apply Errata 2.3 for LoRa mode receving
        if for_rx and bool(self._stngs.get("FLD_RDO_LORA_MODE")):
            bw = self._stngs.get("FLD_LORA_BW")
            if bw >= SX127xSettings.STNG_LORA_BW_500K:
                auto_if_on = True
            else:
                # Adjust the intermediate freq per errata
                if_freq2_lut = (
                    0x48, 0x44, 0x44, 0x44, 0x44, 0x44, 0x40, 0x40, 0x40)
                reg_if_freq2 = if_freq2_lut[bw]
                # Add the rejection offset to the carrier freq
                # and fill the stngs holding array with that
                rejection_offset_hz_lut = (
                    7810, 10420, 15620, 20830, 31250, 41670, 0, 0, 0)
                freq += rejection_offset_hz_lut[bw]

        # If LoRa mode or LoRa BW has changed,
        # apply the errata values to their regs
        if (self._stngs.changed("FLD_RDO_LORA_MODE")
                or self._stngs.changed("FLD_LORA_BW")):
            self._write(SX127x.REG_LORA_IF_FREQ_2, reg_if_freq2)
            reg = self._read(SX127x.REG_LORA_DTCT_OPTMZ)[0]
            reg &= 0x7F
            reg |= (0, 0x80)[auto_if_on]
            self._write(SX127x.REG_LORA_DTCT_OPTMZ, reg)

        # Write outstanding carrier freq to the regs
        if freq != self._stngs.get_applied("FLD_RDO_FREQ"):
            # Adjust numerical frequency to register value
            reg_freq = round(freq * 2**19 / SX127x.SX127X_OSC_FREQ)
            regs = [
                (reg_freq >> 16) & 0xFF,    # MSB
                (reg_freq >> 8) & 0xFF,     # MID
                (reg_freq >> 0) & 0xFF,     # LSB
            ]
            self._write(SX127x.REG_RDO_FREQ_MSB, regs)
            self._stngs_freq_applied = freq


class SX127xSettings():
    """Tracks the register settings for a SX127x radio.
    A settings field is one or more bits that come from a SX127x register,
    but is abstracted out of the register and bit position.  You simply use
    a "FLD_***_***" string to access the field.  This class takes care of
    knowing the field's register, the masking and the shifting.

    When setting a value to a field, the value is validated against min/max
    values.  Also the value is held in a cache of requested field changes
    so that SX127x class can write all modified fields at once
    when the radio is in a good state to do so.
    When that mass-write takes place, only modified fields are
    written and afterward the requested values are considered applied.
    """

    # Radio Frequency limits [Hz]
    STNG_RF_FREQ_MIN = 137000000
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

    # Field info named tuple
    FldInfo = collections.namedtuple(
        "FldInfo",
        "lora_mode reg_start reg_cnt bit_start "
        "bit_cnt val_min val_max val_reset")

    # Field info table
    _fld_info = {
        # field                              lora    reg                             reg     bit     bit     val                 val                 val
        # name                               mode    start                           cnt     start   cnt     min                 max                 reset
        "FLD_RDO_LF_MODE":          FldInfo( False,  SX127x.REG_RDO_OPMODE,          1,      3,      1,      0,                  1,                  1                   ),
        "FLD_RDO_LORA_MODE":        FldInfo( False,  SX127x.REG_RDO_OPMODE,          1,      7,      1,      0,                  1,                  0                   ),
        "FLD_RDO_FREQ":             FldInfo( False,  SX127x.REG_RDO_FREQ_MSB,        3,      0,      8,      STNG_RF_FREQ_MIN,   STNG_RF_FREQ_MAX,   434000000           ),
        "FLD_RDO_OUT_PWR":          FldInfo( False,  SX127x.REG_RDO_PA_CFG,          1,      0,      4,      0,                  15,                 0x0F                ),
        "FLD_RDO_MAX_PWR":          FldInfo( False,  SX127x.REG_RDO_PA_CFG,          1,      4,      3,      0,                  7,                  0x04                ),
        "FLD_RDO_PA_BOOST":         FldInfo( False,  SX127x.REG_RDO_PA_CFG,          1,      7,      1,      0,                  1,                  0                   ),
        "FLD_RDO_LNA_BOOST_HF":     FldInfo( False,  SX127x.REG_RDO_LNA,             1,      0,      2,      0,                  3,                  0                   ),
        "FLD_RDO_LNA_GAIN":         FldInfo( False,  SX127x.REG_RDO_LNA,             1,      5,      3,      1,                  6,                  0x01                ),
        "FLD_RDO_DIO0":             FldInfo( False,  SX127x.REG_RDO_DIOMAP1,         1,      6,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO1":             FldInfo( False,  SX127x.REG_RDO_DIOMAP1,         1,      4,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO2":             FldInfo( False,  SX127x.REG_RDO_DIOMAP1,         1,      2,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO3":             FldInfo( False,  SX127x.REG_RDO_DIOMAP1,         1,      0,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO4":             FldInfo( False,  SX127x.REG_RDO_DIOMAP2,         1,      6,      2,      0,                  2,                  0                   ),
        "FLD_RDO_DIO5":             FldInfo( False,  SX127x.REG_RDO_DIOMAP2,         1,      4,      2,      0,                  2,                  0                   ),

        "FLD_LORA_IMPLCT_HDR_MODE": FldInfo( True,   SX127x.REG_LORA_CFG1,           1,      0,      1,      0,                  1,                  0                   ),
        "FLD_LORA_CR":              FldInfo( True,   SX127x.REG_LORA_CFG1,           1,      1,      3,      STNG_LORA_CR_MIN,   STNG_LORA_CR_MAX,   STNG_LORA_CR_4TO5   ),
        "FLD_LORA_BW":              FldInfo( True,   SX127x.REG_LORA_CFG1,           1,      4,      4,      STNG_LORA_BW_MIN,   STNG_LORA_BW_MAX,   STNG_LORA_BW_125K   ),
        "FLD_LORA_CRC_EN":          FldInfo( True,   SX127x.REG_LORA_CFG2,           1,      2,      1,      0,                  1,                  0                   ),
        "FLD_LORA_SF":              FldInfo( True,   SX127x.REG_LORA_CFG2,           1,      4,      4,      STNG_LORA_SF_MIN,   STNG_LORA_SF_MAX,   STNG_LORA_SF_128_CPS),
        "FLD_LORA_RX_TMOUT":        FldInfo( True,   SX127x.REG_LORA_CFG2,           2,      0,      2,      0,                  (1<<10)-1,          0x00                ),
        "_FLD_LORA_RX_TMOUT_2":     FldInfo( 0,      SX127x.REG_LORA_RX_SYM_TMOUT,   0,      0,      0,      0,                  0,                  0x64                ),
        "FLD_LORA_PREAMBLE_LEN":    FldInfo( True,   SX127x.REG_LORA_PREAMBLE_LEN,   2,      0,      16,     0,                  (1<<16)-1,          0x00                ),
        "_FLD_LORA_PREAMBLE_LEN_2": FldInfo( 0,      SX127x.REG_LORA_PREAMBLE_LEN_LSB,0,     0,      0,      0,                  0,                  0x08                ),
        "FLD_LORA_AGC_ON":          FldInfo( True,   SX127x.REG_LORA_CFG3,           1,      2,      1,      0,                  1,                  0                   ),
        "FLD_LORA_SYNC_WORD":       FldInfo( True,   SX127x.REG_LORA_SYNC_WORD,      1,      0,      8,      0,                  (1<<8)-1,           0x12                ),
    }

    def __init__(self):
        self._stngs = {}
        self._stngs_applied = {}
        self.reset()

# Public

    @classmethod
    def get_field_names(cls):
        return filter(lambda x: not x.startswith("_"), cls._fld_info.keys())

    @classmethod
    def get_reg(cls, fld):
        return cls._fld_info[fld].reg_start

    @classmethod
    def get_reset_value(cls, fld):
        return cls._fld_info[fld].val_reset

    def apply(self, fld):
        """Copies the desired value to the applied value.
        This should be called when the setting is actually
        written to the device register.
        """
        self._stngs_applied[fld] = self._stngs[fld]

    def changed(self, fld):
        """Returns True if the setting field differs
        from the one that's applied.
        """
        return self._stngs[fld] != self._stngs_applied[fld]

    def get(self, fld):
        # Frequency is a special case because it's multi-reg and
        # is handled specially due to chip errata
        if fld == "FLD_RDO_FREQ":
            return self._rdo_stngs_freq
        else:
            return self._stngs[fld]

    def get_applied(self, fld):
        return self._stngs_applied[fld]

    def get_applied_stngs(self):
        return self._stngs_applied

    def modify(self, fld, val):
        """Modifies the given value to clear out the former bits
        for the given field and put the requested value in their place.
        """
        # FIXME: for fields that span >1 register
        if SX127xSettings._fld_info[fld].reg_cnt > 1: return val

        bit_start = self._fld_info[fld].bit_start
        bitf = self._bit_fld(bit_start,
                             self._fld_info[fld].bit_cnt)
        val &= (~bitf & 0xFF)
        val |= (bitf & (self._stngs[fld] << bit_start))
        return val


    def reset(self):
        """Applies the chip-reset values to all of the fields.
        This should be done after a chip reset
        so this driver is synchronized with the chip.
        """
        for fld in self.get_field_names():
            val = self.get_reset_value(fld)
            self._stngs[fld] = val
            self._stngs_applied[fld] = val
        self._rdo_stngs_freq_applied = 0


    def set(self, fld, val):
        """Sets the field to the value.
        The field is not written to the register(s) in this procedure.
        Once all the fields have been set, call write_stngs() to write
        all of the settings to the register(s).
        """
        minval = SX127xSettings._fld_info[fld].val_min
        maxval = SX127xSettings._fld_info[fld].val_max
        assert minval <= val <= maxval, "Invalid value"

        self._stngs[fld] = val

        # Settings special cases for multi-reg values
        if fld == "FLD_RDO_FREQ":
            assert SX127xSettings._fld_info[fld].reg_cnt == 3
            # Errata 2.3: store freq so rejection offset may be applied later
            self._rdo_stngs_freq = val

        elif fld == "FLD_LORA_RX_TMOUT":
            assert SX127xSettings._fld_info[fld].reg_cnt == 2
            self._stngs["FLD_LORA_RX_TMOUT"] = (val >> 8) & 0xFF
            self._stngs["_FLD_LORA_RX_TMOUT_2"] = (val >> 0) & 0xFF

        elif fld == "FLD_LORA_PREAMBLE_LEN":
            assert SX127xSettings._fld_info[fld].reg_cnt == 2
            self._stngs["FLD_LORA_PREAMBLE_LEN"] = (val >> 8) & 0xFF
            self._stngs["_FLD_LORA_PREAMBLE_LEN_2"] = (val >> 0) & 0xFF

        # Settings normal case for single-reg values
        else:
            assert SX127xSettings._fld_info[fld].reg_cnt == 1
            mask = self._bit_fld(0, SX127xSettings._fld_info[fld].bit_cnt)
            self._stngs[fld] = val & mask

# Private

    def _bit_fld(self, ls1, nbits):
        """Creates a bitfield per
        https://stackoverflow.com/questions/8774567/c-macro-to-create-a-bit-mask-possible-and-have-i-found-a-gcc-bug
        """
        assert nbits <= 8
        return ((0xFF >> (7 - ((ls1) + (nbits) - 1))) & ~((1 << (ls1)) - 1))
