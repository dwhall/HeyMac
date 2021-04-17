"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Radio Settings model and view.
"""

from asciimatics.exceptions import NextScene
from asciimatics.widgets import Button, DropdownList, Frame, Layout, Text

from heymac.phy import SX127xSettings


class RadioStngsView(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="Radio Settings",
                         can_scroll=True,
                         reduce_cpu=True)
        self._stngs_model = model

        # Layout the settings widgets
        layout1 = Layout([1,2,1], fill_frame=True)
        self.add_layout(layout1)
        layout1.add_widget(DropdownList(
                            [("LoRa", 1),],
                            label="Radio Mode:",
                            name="radio_mode",
                            disabled=True), 1)
        layout1.add_widget(Text(
                            label="RF Freq [KHz]:",
                            name="rf_freq",
                            on_change=self._on_change,
                            validator=self._is_valid_freq), 1)
        layout1.add_widget(DropdownList(
                            [
                                ("4:5", SX127xSettings.STNG_LORA_CR_4TO5),
                                ("4:6", SX127xSettings.STNG_LORA_CR_4TO6),
                                ("4:7", SX127xSettings.STNG_LORA_CR_4TO7),
                                ("4:8", SX127xSettings.STNG_LORA_CR_4TO8),
                            ],
                            label="Code Rate:",
                            name="code_rate"), 1)
        layout1.add_widget(DropdownList(
                            [
                                (" 7.8  KHz", SX127xSettings.STNG_LORA_BW_7K8),
                                ("10.4  KHz", SX127xSettings.STNG_LORA_BW_10K4),
                                ("15.6  KHz", SX127xSettings.STNG_LORA_BW_15K6),
                                ("20.8  KHz", SX127xSettings.STNG_LORA_BW_20K8),
                                ("31.25 KHz", SX127xSettings.STNG_LORA_BW_31K25),
                                ("41.7  KHz", SX127xSettings.STNG_LORA_BW_41K7),
                                ("62.5  KHz", SX127xSettings.STNG_LORA_BW_62K5),
                                ("125   KHz", SX127xSettings.STNG_LORA_BW_125K),
                                ("250   KHz", SX127xSettings.STNG_LORA_BW_250K),
                                ("500   KHz", SX127xSettings.STNG_LORA_BW_500K),
                            ],
                            label="Bandwidth:",
                            name="bandwidth"), 1)
        layout1.add_widget(DropdownList(
                            [
                                ("  64 cps", SX127xSettings.STNG_LORA_SF_64_CPS),
                                (" 128 cps", SX127xSettings.STNG_LORA_SF_128_CPS),
                                (" 256 cps", SX127xSettings.STNG_LORA_SF_256_CPS),
                                (" 512 cps", SX127xSettings.STNG_LORA_SF_512_CPS),
                                ("1024 cps", SX127xSettings.STNG_LORA_SF_1024_CPS),
                                ("2048 cps", SX127xSettings.STNG_LORA_SF_2048_CPS),
                                ("4096 cps", SX127xSettings.STNG_LORA_SF_4096_CPS),
                            ],
                            label="Spread Factor:",
                            name="spread_factor"), 1)

        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Apply",
                                  on_click=self._on_click_apply), 1)
        layout2.add_widget(Button("Cancel", self._on_click_cancel), 2)

        self.fix()


    def reset(self):
        super().reset()
        self.data = self._stngs_model.get_stngs()


    def _is_valid_freq(self, freq_khz_str):
        try:
            freq_hz = 1000 * int(freq_khz_str)
            return (SX127xSettings.STNG_RF_FREQ_MIN
                    <= freq_hz
                    <= SX127xSettings.STNG_RF_FREQ_MAX)
        except:
            return False


    def _on_change(self):
        self.save()
        self._update_disabled()

    def _update_disabled(self):
        pass


    def _on_click_apply(self):
        self.save()
        self._stngs_model.apply_stngs(self.data)
        raise NextScene("Messages")


    def _on_click_cancel(self):
        raise NextScene("Messages")

