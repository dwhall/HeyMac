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
        self._msg_data = []

    def _rx_clbk(self, hm_frame):
        # TODO: blip status RX indicator
        if isinstance(hm_frame, HeymacCmdCsmaBcn):
            longaddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            callsign = "TODO"  # FIXME: get callsign from beacon (doesn't exist in std beacon)
            self._bcn_ident[longaddr] = callsign

        elif isinstance(hm_frame, HeymacCmdTxt):
            rxtime = hm_frame.rx_meta[0]
            src = hm_frame.saddr
            msg = hm_frame.cmd.get_field(hm_frame.cmd.FLD_MSG)
            self.add_msg(rxtime, src, msg)


    def add_msg(self, tm, src, msg):
        bisect.insort(self._msg_data, (tm, src, msg))


    def send_msg(self, msg):
        """Requests the link layer transmit the given message"""
        txt_cmd = HeymacCmdTxt(FLD_MSG=msg.encode())
        self._lnk_hsm.send_cmd(txt_cmd)


    def get_msgs(self):
        return self._msg_data.copy()


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
        msgs = self._msgs_model.get_msgs()
        msgs_widget = self.find_widget("msgs")
        msgs_widget.options = self._format_msgs(msgs)

    def _format_msgs(self, msgs):
        height = self.find_widget("msgs")._h
        msgs_data = self._msgs_model.get_msgs()
        len_msgs_data = len(msgs_data)
        if len_msgs_data < height:
            msgs_to_show = msgs_data
        else:
            msgs_to_show = msgs_data[len_msgs_data - height + 1:]
        msg_list = []
        for n, msg_data in enumerate(msgs_to_show):
            msg_list.append((msg_data, n+1))
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

            tm_str = time.strftime("%H:%M:%S", time.localtime())
            ident = self._ident_model.get_ident()
            self._msgs_model.add_msg(tm_str, ident["callsign"], msg)
            self._updt_msgs()

    def _get_and_clear_msg_input(self):
        widget = self.find_widget("msg_input")
        msg = widget.value
        widget.value = ""
        return msg
