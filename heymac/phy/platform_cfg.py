"""
Copyright 2021 Dean Hall.  See LICENSE for details.
"""

class SpiConfig:
    """SPI bus configuration info.

    This info is platform-specific.  It is set once and read-only thereafter.

    Port (usually 0 or 1).
    CS Chip Select (usually 0 or 1).
    Frequency in Hertz (an int value usually between 1,000,000 and 20,000,000).
    """
    # SPI clock frequency limits
    SPI_FREQ_MIN = 1_000_000
    SPI_FREQ_MAX = 20_000_000

    def __init__(self, port, cs, freq):
        assert port in (0, 1), "SPI port index must be 0 or 1"
        assert cs in (0, 1), "SPI chip select must be 0 or 1"
        assert SpiConfig.SPI_FREQ_MIN <= freq <= SpiConfig.SPI_FREQ_MAX, \
            "SPI clock frequency should be within 1-20 MHz"
        self._port = int(port)
        self._cs = int(cs)
        self._freq = int(freq)

    @property
    def port(self):
        return self._port

    @property
    def cs(self):
        return self._cs

    @property
    def freq(self):
        return self._freq


class DioConfig:
    """DIO Configuration info.

    DIO1-5 pins exist on the LoRa chip.  Here you define which CPU pins
    connect to those DIO pins.  This info is platform-specific.
    It is set once and read-only thereafter.
    """
    def __init__(self, dio0=None, dio1=None, dio2=None, dio3=None, dio4=None,
                 dio5=None):
        assert (dio0 and dio1 and dio3), "Heymac requires DIO0, DIO1 and DIO3."
        self._pins = (dio0, dio1, dio2, dio3, dio4, dio5)
        for pin_nmbr in self._pins:
            assert 0 <= pin_nmbr <= 48, "Not a valid RPi GPIO number"

    @property
    def pins(self):
        return self._pins


class ResetConfig:
    """Reset Configuration info.

    The Reset pin exists on the LoRa chip.  Here you define which CPU pin
    connects to the LoRa reset pin.  This info is platform-specific.
    It is set once and read-only thereafter.
    """
    def __init__(self, pin, pin_low_time=0.000110, after_reset_wait=0.005):
        assert 0 <= pin <= 48, "Not a valid RPi GPIO number"
        self._pin = pin
        self._pin_low_time = pin_low_time
        self._after_reset_wait = after_reset_wait

    @property
    def pin(self):
        return self._pin

    @property
    def pin_low_time(self):
        return self._pin_low_time

    @property
    def after_reset_wait(self):
        return self._after_reset_wait