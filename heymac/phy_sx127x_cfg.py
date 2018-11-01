#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.
"""


import collections
import time


class SX127xConfig(object):
    """Reads, sets and writes configurable values to/from the SX127x device
    """
    def __init__(self, **cfg_dict):
        cfg_items = ("bandwidth", "code_rate", "implct_hdr_mode",
            "spread_factor", "tx_cont", "en_crc", "symbol_count",
            "preamble_len", "en_ldr", "agc_auto", "sync_word")

        # All configurable items are kept in this dict
        self.cfg_dict = {}

        # For each item given to the constructor,
        # check that it is a configurable item and
        # set the item via the setter (which will validate the value)
        for k,v in cfg_dict.items():
            assert k in cfg_items
            setattr(self, k, v)

    @property
    def bandwidth(self,):
        return self.cfg_dict.get("bandwidth", None)

    @bandwidth.setter
    def bandwidth(self, val):
        """Validates and sets bandwidth.
        """
        bandwidth_lut = {
            7810: 0b0000,
            10420: 0b0001,
            15620: 0b0010,
            20830: 0b0011,
            31250: 0b0100,
            41670: 0b0101,
            62500: 0b0110,
            125000: 0b0111,
            250000: 0b1000,
            500000: 0b1001}
        bandwidth_options = list(bandwidth_lut.keys())
        bandwidth_options.sort()
        assert val in bandwidth_options, "bandwidth must be one of: " + str(bandwidth_options)
        self.cfg_dict["bandwidth"] = val
        self.bandwidth_idx = bandwidth_lut[val]


    @property
    def code_rate(self,):
        return self.cfg_dict.get("code_rate", None)

    @code_rate.setter
    def code_rate(self, val):
        """Validates and sets code_rate.
        """
        code_rate_lut = {
            "4/5": 0b001,
            "4/6": 0b010,
            "4/7": 0b011,
            "4/8": 0b100}
        code_rate_options = list(code_rate_lut.keys())
        code_rate_options.sort()
        assert val in code_rate_options, "code_rate must be one of: " + str(code_rate_options)
        self.cfg_dict["code_rate"] = val
        self.code_rate_idx = code_rate_lut[val]


    @property
    def implct_hdr_mode(self,):
        return self.cfg_dict.get("implct_hdr_mode", None)

    @implct_hdr_mode.setter
    def implct_hdr_mode(self, val):
        """Validates and sets implct_hdr_mode.
        """
        assert type(val) is bool
        self.cfg_dict["implct_hdr_mode"] = val


    @property
    def spread_factor(self,):
        return self.cfg_dict.get("spread_factor", None)

    @spread_factor.setter
    def spread_factor(self, val):
        """Validates and sets spread_factor.
        """
        spread_factor_lut = {
            64: 6,
            128: 7,
            256: 8,
            512: 9,
            1024: 10,
            2048: 11,
            4096: 12}
        spread_factor_options = list(spread_factor_lut.keys())
        spread_factor_options.sort()
        assert val in spread_factor_options, "spread_factor must be one of: " + str(spread_factor_options)
        self.cfg_dict["spread_factor"] = val
        self.spread_factor_idx = spread_factor_lut[val]


    @property
    def tx_cont(self,):
        return self.cfg_dict.get("tx_cont", None)

    @tx_cont.setter
    def tx_cont(self, val):
        """Validates and sets tx_cont.
        """
        assert type(val) is bool
        self.cfg_dict["tx_cont"] = val


    @property
    def en_crc(self,):
        return self.cfg_dict.get("en_crc", None)

    @en_crc.setter
    def en_crc(self, val):
        """Validates and sets en_crc.
        """
        assert type(val) is bool
        self.cfg_dict["en_crc"] = val


    @property
    def symbol_count(self,):
        return self.cfg_dict.get("symbol_count", None)

    @symbol_count.setter
    def symbol_count(self, val):
        """Validates and sets symbol_count.
        """
        assert type(val) is int, "symbol_count must be a whole number"
        assert 0 <= val <= 2**10 - 1, "symbol_count must be within the range 0 .. 1023, inclusive"
        self.cfg_dict["symbol_count"] = val

    def set_rx_timeout(self, secs):
        """Calculates the symbol_count property to achieve the desired timeout
        given in seconds (float)
        """
        assert type(secs) in (int, float)

        symbol_rate = self.bandwidth / 2**self.spread_factor_idx
        self.symbol_count = round(secs * symbol_rate)


    @property
    def preamble_len(self,):
        return self.cfg_dict.get("preamble_len", None)

    @preamble_len.setter
    def preamble_len(self, val):
        """Validates and sets preamble_len.
        """
        assert 7 <= val <= 65535, "preamble_len must be within the range 7 .. 65535, inclusive"
        self.cfg_dict["preamble_len"] = val


    @property
    def en_ldr(self,):
        return self.cfg_dict.get("en_ldr", None)

    @en_ldr.setter
    def en_ldr(self, val):
        """Validates and sets en_ldr.
        """
        assert type(val) is bool
        self.cfg_dict["en_ldr"] = val


    @property
    def agc_auto(self,):
        return self.cfg_dict.get("agc_auto", None)

    @agc_auto.setter
    def agc_auto(self, val):
        """Validates and sets agc_auto.
        """
        assert type(val) is bool
        self.cfg_dict["agc_auto"] = val


    @property
    def sync_word(self,):
        return self.cfg_dict.get("sync_word", None)

    @sync_word.setter
    def sync_word(self, val):
        """Validates and sets sync_word.
        """
        assert 0 <= val <= 255, "sync_word must be within the range 0 .. 255, inclusive"
        self.cfg_dict["sync_word"] = val
