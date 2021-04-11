"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Messages model and view.
The Messages view is the root screen.
"""

import bisect
import time

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import NextScene, ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Frame, Label, Layout, \
        MultiColumnListBox, Text, Widget

from heymac.lnk import HeymacCmdCsmaBcn, HeymacCmdTxt


class MsgsView(Frame):
    def __init__(self, screen):
        super().__init__(
                screen,
                screen.height,
                screen.width,
                title="HeyMac",
                hover_focus=True,
                can_scroll=True)

        # Received messages area
        layout1 = Layout([100], fill_frame=True)
        self.add_layout(layout1)

        # Message-to-send input area
        self._msg_input = Text(
                label="Input:",
                name="msg_input",
                max_length=200)
        layout1.add_widget(self._msg_input)

        self.fix()

    def process_event(self, tui_event):
        if tui_event is not None and isinstance(tui_event, KeyboardEvent):
            if tui_event.key_code == 13:
                if self.find_widget("msg_input") == self.focussed_widget:
                    self._send_msg()
        return super().process_event(tui_event)

    def _send_msg(self):
        print("Mock send msg")


def demo(screen, scene):
    scenes = [
        Scene([MsgsView(screen)], -1, name="Main")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)

last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
