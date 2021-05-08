"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Radio Status view.
"""

from asciimatics.exceptions import NextScene
from asciimatics.widgets import Button, Frame, Label, Layout, Text


class StatusView(Frame):
    def __init__(self, screen, status_model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="Status",
                         can_scroll=False,
                         reduce_cpu=True)
        self._status_model = status_model

        # Layout the status widgets
        layout1 = Layout([1, 4, 1], fill_frame=False)
        self.add_layout(layout1)
        layout1.add_widget(Label(label="Status page is under construction"), 1)
        layout1.add_widget(Text(label="GPS:",
                                name="gps",
                                readonly=True,
                                disabled=True), 1)

        layout1.add_widget(Button("Return", self._on_click_return), 1)
        self.fix()

    def _on_click_return(self):
        raise NextScene("Messages")


    def update_gps(self, nmea_sntnc):
        w = self.find_widget("gps")
        w.value = nmea_sntnc.strip()
        self.update(0)
