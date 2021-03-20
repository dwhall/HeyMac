#!/usr/bin/env python3

import logging
import sys

from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Button, DropdownList, Frame, Label, Layout, \
    ListBox, MultiColumnListBox, Text, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import farc

import lnk_heymac
import phy_sx127x

UI_ANIMATE_PERIOD = 0.050  # Taken from asciimatics screen.py


# Models

class MsgsModel(object):
    def __init__(self, lnk_sm):
        self._lnk_sm = lnk_sm
        self._lnk_sm.set_rx_clbk(self._rx_clbk)
        self._bcn_ident = {}
        self._msg_model = []

    def send_msg(self, msg):
        """Requests the link layer transmit the given message"""
        # TODO: also updates the msgs view with the sent msg
        pass

    def get_msgs(self):
        """Returns a list of the displayable data"""
        msgs = self._msg_model.copy()
        # TODO: sort by time
        # TODO: convert time
        # TODO: convert saddr to callsign
        return msgs

    def _rx_clbk(self, hm_frame):
        # TODO: blip status RX indicator
        if isinstance(hm_frame, lnk_heymac.HeymacCmdCsmaBcn):
            longaddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            callsign = "TODO"  # FIXME: get callsign from beacon (doesn't exist in std beacon)
            self._bcn_ident[longaddr] = callsign

        elif isinstance(hm_frame, lnk_heymac.HeymacCmdTxt):
            rxtime = hm_frame.rx_meta[0]
            src = hm_frame.saddr
            msg = hm_frame.cmd.get_field(hm_frame.cmd.FLD_MSG)
            self._msg_model.append((rxtime, src, msg))


class StatusModel(object):
    def __init__(self, phy_sm):
        self._phy_sm = phy_sm

    def get_status(self):
        # TODO: get data dynamically
        data = {"time": "14:56:42",
                "stngs": "(9000 8N1)",
                "flags": "[--------]",
                "txrx": "--/rx",
                }
        return data

    def get_status_flags(self):
        data = self.get_status()
        return data["flags"]


class RadioStngsModel(object):
    def __init__(self, phy_sm):
        self._phy_sm = phy_sm

    def apply_stngs(self, model_stngs):
        stng_fld = {
            "radio_mode": "FLD_RDO_LORA_MODE",
            "rf_freq": "FLD_RDO_FREQ",
            "code_rate": "FLD_LORA_CR",
            "bandwidth": "FLD_LORA_BW",
            "spread_factor": "FLD_LORA_SF",
        }
        stngs = []
        for model_name, val in model_stngs.items():
            if model_name == "rf_freq":
                val = 1000*int(val)
            stngs.append((stng_fld[model_name], val))
        # FIXME: phy is expecting a complete list stngs (not just what the model can adjust)
        #       ? change phy to use dict as stngs container ?
        self._phy_sm.set_dflt_stngs(stngs)

    def get_stngs(self):
        model_name = {
            "FLD_RDO_LORA_MODE": "radio_mode",
            "FLD_RDO_FREQ": "rf_freq",
            "FLD_LORA_CR": "code_rate",
            "FLD_LORA_BW": "bandwidth",
            "FLD_LORA_SF": "spread_factor",
        }
        model_flds = model_name.keys()
        model_stngs = {}
        for stng_fld, val in self._phy_sm.get_stngs():
            if stng_fld in model_flds:
                if model_name[stng_fld] == "rf_freq":
                    val = str(val // 1000)
                model_stngs[model_name[stng_fld]] = val
        return model_stngs


# Views

class MsgsView(Frame):
    def __init__(self, screen, msgs_model, status_model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="HeyMac",
                         on_load=self._updt_msgs,
                         hover_focus=True,
                         can_scroll=True)
        self._msgs_model = msgs_model
        self._status_model = status_model

        # Received messages area
        layout1 = Layout([100], fill_frame=True)
        self.add_layout(layout1)
        self._msgs_box = MultiColumnListBox(
            Widget.FILL_FRAME,
            [9, 12, 0],
            [(["00:00:00", "KC4KSU", "Hello"], 1)],
            name="msgs",
            titles=["Time", "From", "Message"],
            add_scroll_bar=True)
        self._msgs_box.disabled = True
        layout1.add_widget(self._msgs_box)

        # Message-to-send input area
        layout2 = Layout([100])
        self.add_layout(layout2)
        self._msg_input = Text(
            label="Callsign",
            name="msg_input",
            on_change=self._on_input_change,
            max_length=200)
        layout2.add_widget(self._msg_input)

        # Interactive status bar
        layout3 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout3)
        self._time = Label("00:00:00", name="time")
        self._ident = Button(
            "No Ident",
            self._on_click_ident,
            name="ident")
        self._stngs = Button(
            "No Stngs",
            self._on_click_stngs,
            name="stngs")
        self._status = Button(
            "No Status",
            self._on_click_status)
        self._txrx = Label("--/--", name="txrx")
        layout3.add_widget(self._time, 0)
        layout3.add_widget(self._ident, 1)
        layout3.add_widget(self._stngs, 2)
        layout3.add_widget(self._status, 3)
        layout3.add_widget(self._txrx, 4)

        self.fix()
        self._on_input_change()

    def process_event(self, tui_event):
        if tui_event is not None and isinstance(tui_event, KeyboardEvent):
            if tui_event.key_code == Screen.KEY_F2:
                self._on_click_stngs()
                # IDEA: self.post_fifo(farc.Event(farc.Signal._UI_KEYCODE, tui_evt.key_code))
        return super().process_event(tui_event)

    def _on_input_change(self):
        pass

    def _updt_msgs(self):
        msgs = self._msgs_model.get_msgs()

    def _send_msg(self, msg):
        pass

    def _on_click_ident(self):
        pass

    def _on_click_status(self):
        pass

    def _on_click_stngs(self):
        raise NextScene("Settings")

    @staticmethod
    def _quit():
        raise StopApplication("User quit")


class RadioStngsView(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         hover_focus=True,
                         can_scroll=True,
                         title="Radio Settings",
                         reduce_cpu=True)
        # Save reference to the model
        self._stngs_model = model

        # Create the form for displaying the list of contacts.
        layout = Layout([1,2,1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(DropdownList(
                            [("LoRa", 1),],
                            label="Radio Mode:",
                            name="radio_mode"), 1)
        layout.add_widget(Text(
                            label="RF Freq [KHz]:",
                            name="rf_freq",
                            validator=self._is_valid_freq), 1)
        layout.add_widget(DropdownList(
                            [
                                ("4:5", phy_sx127x.PhySX127xSettings.STNG_LORA_CR_4TO5),
                                ("4:6", phy_sx127x.PhySX127xSettings.STNG_LORA_CR_4TO6),
                                ("4:7", phy_sx127x.PhySX127xSettings.STNG_LORA_CR_4TO7),
                                ("4:8", phy_sx127x.PhySX127xSettings.STNG_LORA_CR_4TO8),
                            ],
                            label="Code Rate:",
                            name="code_rate"), 1)
        layout.add_widget(DropdownList(
                            [
                                (" 7.8  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_7K8),
                                ("10.4  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_10K4),
                                ("15.6  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_15K6),
                                ("20.8  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_20K8),
                                ("31.25 KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_31K25),
                                ("41.7  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_41K7),
                                ("62.5  KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_62K5),
                                ("125   KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_125K),
                                ("250   KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_250K),
                                ("500   KHz", phy_sx127x.PhySX127xSettings.STNG_LORA_BW_500K),
                            ],
                            label="Bandwidth:",
                            name="bandwidth"), 1)
        layout.add_widget(DropdownList(
                            [
                                ("  64 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_64_CPS),
                                (" 128 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_128_CPS),
                                (" 256 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_256_CPS),
                                (" 512 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_512_CPS),
                                ("1024 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_1024_CPS),
                                ("2048 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_2048_CPS),
                                ("4096 cps", phy_sx127x.PhySX127xSettings.STNG_LORA_SF_4096_CPS),
                            ],
                            label="Spread Factor:",
                            name="spread_factor"), 1)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Apply", self._apply), 1)
        layout2.add_widget(Button("Cancel", self._cancel), 2)
        self.fix()

    def reset(self):
        super().reset()
        self.data = self._stngs_model.get_stngs()

    def _apply(self):
        self.save()
        self._stngs_model.apply_stngs(self.data)
        raise NextScene("Msgs")

    @staticmethod
    def _is_valid_freq(freq_str_khz):
        try:
            freq = 1000 * int(freq_str_khz)
            return (phy_sx127x.PhySX127xSettings.STNG_RF_FREQ_MIN
                    <= freq
                    <= phy_sx127x.PhySX127xSettings.STNG_RF_FREQ_MAX)
        except:
            return False

    @staticmethod
    def _cancel():
        raise NextScene("Msgs")


# State Machine


class TxtUiAhsm(farc.Ahsm):
    def __init__(self, phy_sm, lnk_sm):
        """Language-specific initialization."""
        super().__init__()
        self._msgs_model = MsgsModel(lnk_sm)
        self._status_model = StatusModel(phy_sm)
        self._stngs_model = RadioStngsModel(phy_sm)

    @farc.Hsm.state
    def _initial(self, event):
        """PseudoState: _initial

        State machine framework initialization
        """
        farc.Signal.register("_UI_KEYCODE")
        self._tmout_evt = farc.TimeEvent("_UI_TMOUT")

        # UI one-time setup
        screen = Screen.open()
        screen.clear()
        scenes = [
#            Scene([MsgsView(screen, self._msgs_model, self._status_model)], -1, name="Msgs"),
            Scene([RadioStngsView(screen, self._stngs_model)], -1, name="Settings"),
            Scene([MsgsView(screen, self._msgs_model, self._status_model)], -1, name="Msgs"),
        ]
        screen.set_scenes(scenes)
        self._screen = screen
        return self.tran(self._running)


    @farc.Hsm.state
    def _running(self, event):
        """State: _running

        Application init and running.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("UI._running")
            self._tmout_evt.post_in(self, 0)
            self._prev_tick = farc.Framework._event_loop.time()
            return self.handled(event)

        elif sig == farc.Signal._UI_TMOUT:
            # Draw frame
            try:
                self._screen.draw_next_frame()
            except ResizeScreenError as e:
                self._last_scene = e.scene # FIXME: this does nothing
            except StopApplication:
                return self.tran(self._exiting)

            # Iterate immediately if this step took too long
            now = farc.Framework._event_loop.time()
            if now > self._prev_tick + UI_ANIMATE_PERIOD:
                self._tmout_evt.post_in(self, 0)
                self._prev_tick = now

            # otherwise iterate one period later
            else:
                self._prev_tick += UI_ANIMATE_PERIOD
                self._tmout_evt.post_at(self, self._prev_tick)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _exiting(self, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("UI._exiting")
            self._screen.close()
            sys.exit(0)
            return self.handled(event)

        return self.super(self.top)
