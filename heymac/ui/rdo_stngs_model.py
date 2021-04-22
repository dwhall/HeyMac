"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Radio Settings model and view.
"""

from ..phy import SX127xSettings


class RadioStngsModel(object):
    def __init__(self, phy_hsm):
        self._phy_hsm = phy_hsm


    def apply_stngs(self, model_stngs):
        stng_fld = {
            "radio_mode": "FLD_RDO_LORA_MODE",
            "rf_freq": "FLD_RDO_FREQ",
            "code_rate": "FLD_LORA_CR",
            "bandwidth": "FLD_LORA_BW",
            "spread_factor": "FLD_LORA_SF",
        }
        stngs = {}
        for model_name, val in model_stngs.items():
            if model_name == "rf_freq":
                val = 1000 * int(val)
            stngs[stng_fld[model_name]] = val
        self._phy_hsm.update_base_stngs(stngs)


    def get_stngs(self):
        model_name = {
            "FLD_RDO_LORA_MODE": "radio_mode",
            "FLD_RDO_FREQ": "rf_freq",
            "FLD_LORA_CR": "code_rate",
            "FLD_LORA_BW": "bandwidth",
            "FLD_LORA_SF": "spread_factor",
        }
        model_stngs = {}
        phy_stngs = self._phy_hsm.get_stngs()
        for fld, val in phy_stngs.items():
            if fld in model_name:
                if model_name[fld] == "rf_freq":
                    val = str(val // 1000)
                model_stngs[model_name[fld]] = val
        return model_stngs


    def get_summary(self):
        bw = {
            SX127xSettings.STNG_LORA_BW_7K8: ", 7.8 KHz",
            SX127xSettings.STNG_LORA_BW_10K4: ", 10.4 KHz",
            SX127xSettings.STNG_LORA_BW_15K6: ", 15.6 KHz",
            SX127xSettings.STNG_LORA_BW_20K8: ", 20.8 KHz",
            SX127xSettings.STNG_LORA_BW_31K25: ", 31.25 KHz",
            SX127xSettings.STNG_LORA_BW_41K7: ", 41.7 KHz",
            SX127xSettings.STNG_LORA_BW_62K5: ", 62.5 KHz",
            SX127xSettings.STNG_LORA_BW_125K: ", 125 KHz",
            SX127xSettings.STNG_LORA_BW_250K: ", 250 KHz",
            SX127xSettings.STNG_LORA_BW_500K: ", 500 KHz",
        }
        stngs = self.get_stngs()
        if stngs:
            freq = stngs.get("rf_freq", "NoFreq")
            bw = bw.get(stngs.get("bandwidth", None), ", NoBW")
            return freq + bw
        return "NoStngs"
