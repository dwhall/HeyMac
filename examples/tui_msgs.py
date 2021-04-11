"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Messages model and view.
The Messages view is the root screen.
"""

import bisect
import time

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import NextScene, StopApplication
from asciimatics.widgets import Button, Frame, Label, Layout, \
        MultiColumnListBox, Text, Widget
from asciimatics.screen import Screen

from heymac.lnk import HeymacCmdCsmaBcn, HeymacCmdTxt


class MsgsModel(object):
    def __init__(self, lnk_hsm):
        self._lnk_hsm = lnk_hsm
        self._lnk_hsm.set_rx_clbk(self._rx_clbk)
        self._bcn_ident = {}
        self._callsigns = {}
        self._msg_data = []
        self._update_view = None


    def _rx_clbk(self, hm_frame):
        # TODO: blink status RX indicator
        if isinstance(hm_frame.cmd, HeymacCmdCsmaBcn):
            # FIXME: get callsign from beacon (doesn't exist in std beacon)
            longaddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            callsign = "GOTIT"
            self._callsigns[longaddr] = callsign

        elif isinstance(hm_frame.cmd, HeymacCmdTxt):
            rxtime = time.time()
            saddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            msg = hm_frame.cmd.get_field(hm_frame.cmd.FLD_MSG)
            bisect.insort(self._msg_data, (rxtime, saddr, msg.decode()))

        if self._update_view:
            self._update_view()


    def get_callsigns(self):
        return self._callsigns


    def get_latest_msgs(self, n=0):
        return self._msg_data[-n:]


    def send_msg(self, msg):
        """Requests the link layer transmit the given message"""
        txt_cmd = HeymacCmdTxt(FLD_MSG=msg.encode())
        self._lnk_hsm.send_cmd(txt_cmd)

        txtime = time.time()
        saddr = self._lnk_hsm.get_lnk_addr()
        bisect.insort(self._msg_data, (txtime, saddr, msg))


    def set_update_clbk(self, clbk):
        self._update_view = clbk


class MsgsView(Frame):
    def __init__(self, screen, msgs_model, ident_model, stngs_model, status_model):
        super().__init__(
                screen,
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
                [],
                name="msgs",
                titles=["Time", "From", "Message"])
        self._msgs_box.disabled = True
        self._msgs_box.custom_colour = "title"
        layout1.add_widget(self._msgs_box)
        self._msgs_model.set_update_clbk(self._updt_msgs)

        # Message-to-send input area
        layout2 = Layout([100])
        self.add_layout(layout2)
        self._msg_input = Text(
                label="Send:",
                name="msg_input",
                on_change=self._on_input_change,
                max_length=200)
        layout2.add_widget(self._msg_input)

        # Activity bar
        layout3 = Layout([1, 1, 1, 1, 1, 1])
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
                self._status_model.get_summary(),
                self._on_click_status)
        self._txrx = Label("--/--", name="txrx")
        self._quit = Button("Quit", self._on_click_quit)
        layout3.add_widget(self._time, 0)
        layout3.add_widget(self._ident, 1)
        layout3.add_widget(self._stngs, 2)
        layout3.add_widget(self._status, 3)
        layout3.add_widget(self._txrx, 4)
        layout3.add_widget(self._quit, 5)

        self.fix()
        self._on_input_change()

    def _on_input_change(self):
        pass

    def _updt_msgs(self):
        self._msgs_box.options = self._format_msgs()
        self._stngs.text = self._stngs_model.get_summary()

    def _format_msgs(self):
        height = self.find_widget("msgs")._h
        msgs_data = self._msgs_model.get_latest_msgs(height-1)
        callsigns = self._msgs_model.get_callsigns()
        ident = self._ident_model.get_ident()
        callsigns[ident["saddr"]] = ident["callsign_ssid"]
        msg_list = []
        for n, msg_data in enumerate(msgs_data):
            tm, saddr, msg = msg_data
            display_tm = time.strftime("%H:%M:%S", time.localtime(tm))
            display_src = callsigns.get(saddr, saddr.hex()[:8])
            display_msg_data = (display_tm, display_src, msg)
            msg_list.append((display_msg_data, n+1))
        return msg_list


    def _on_click_ident(self):
        raise NextScene("Identity")

    def _on_click_status(self):
        raise NextScene("Status")

    def _on_click_stngs(self):
        raise NextScene("Settings")

    def _on_click_quit(self):
        raise StopApplication("User quit")


    def process_event(self, tui_event):
        if tui_event is not None and isinstance(tui_event, KeyboardEvent):
            if tui_event.key_code == Screen.KEY_F2:
                self._on_click_stngs()
            elif tui_event.key_code in (10, 13):
                if self.find_widget("msg_input") == self.focussed_widget:
                    self._send_msg()
        return super().process_event(tui_event)

    def _send_msg(self):
        msg = self._get_and_clear_msg_input()
        if msg:
            self._msgs_model.send_msg(msg)
            self._updt_msgs()

    def _get_and_clear_msg_input(self):
        widget = self.find_widget("msg_input")
        msg = widget.value
        widget.value = ""
        return msg
