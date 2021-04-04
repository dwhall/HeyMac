#!/usr/bin/env python3

"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Messages model and view.
The Messages view is the root screen.
"""

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import NextScene, StopApplication
from asciimatics.widgets import Button, Frame, Label, Layout, \
        MultiColumnListBox, Text, Widget
from asciimatics.screen import Screen

import heymac


class StatusModel(object):
    def __init__(self, phy_hsm):
        self._phy_hsm = phy_hsm

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


class MsgsModel(object):
    def __init__(self, lnk_hsm):
        self._lnk_hsm = lnk_hsm
        self._lnk_hsm.set_rx_clbk(self._rx_clbk)
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
        if isinstance(hm_frame, heymac.lnk.HeymacCmdCsmaBcn):
            longaddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            callsign = "TODO"  # FIXME: get callsign from beacon (doesn't exist in std beacon)
            self._bcn_ident[longaddr] = callsign

        elif isinstance(hm_frame, heymac.lnk.HeymacCmdTxt):
            rxtime = hm_frame.rx_meta[0]
            src = hm_frame.saddr
            msg = hm_frame.cmd.get_field(hm_frame.cmd.FLD_MSG)
            self._msg_model.append((rxtime, src, msg))


class MsgsView(Frame):
    def __init__(self, screen, msgs_model, ident_model, stngs_model, status_model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="HeyMac",
                         on_load=self._updt_msgs,
                         hover_focus=True,
                         can_scroll=True)
        self._msgs_model = msgs_model
        self._ident_model = ident_model
        self._stngs_model = stngs_model
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
            label="Input:",
            name="msg_input",
            on_change=self._on_input_change,
            max_length=200)
        layout2.add_widget(self._msg_input)

        # Interactive status bar
        layout3 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout3)
        self._time = Label("00:00:00", name="time")
        self._ident = Button(
            self._ident_model.get_summary(),
            self._on_click_ident,
            name="ident")
        self._stngs = Button(
            self._stngs_model.get_summary(),
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
            elif tui_event.key_code == 13:
                if self.find_widget("msg_input") == self.focussed_widget:
                    self._send_msg()
        return super().process_event(tui_event)

    def _on_input_change(self):
        pass

    def _updt_msgs(self):
        msgs = self._msgs_model.get_msgs()

    def _send_msg(self):
        widget = self.find_widget("msg_input")
        msg = widget.value
        widget.reset() # FIXME
        self._msgs_model.send_msg(msg)


    def _on_click_ident(self):
        raise NextScene("Identity")

    def _on_click_status(self):
        pass

    def _on_click_stngs(self):
        raise NextScene("Settings")

    def _quit(self):
        raise StopApplication("User quit")
