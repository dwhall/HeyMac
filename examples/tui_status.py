"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Radio Status model and view.
"""

from asciimatics.exceptions import NextScene
from asciimatics.widgets import Button, Divider, Frame, Label, Layout, Text, Widget
from asciimatics.screen import Screen


class RadioStatusModel(object):
    def __init__(self, phy_hsm):
        self._phy_hsm = phy_hsm


    def get_summary(self):
        return "--------"


class RadioStatusView(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         hover_focus=True,
                         can_scroll=True,
                         title="Radio Status",
                         reduce_cpu=True)
        self._status_model = model

        # Layout the status widgets
        layout1 = Layout([1,2,1], fill_frame=False)
        self.add_layout(layout1)
        layout1.add_widget(Label(label="Status page is under construction"), 1)

        layout1.add_widget(Button("Return", self._on_click_return), 1)
        self.fix()


    def _on_click_return(self):
        raise NextScene("Messages")
