#!/usr/bin/env python3

"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface state machine
"""

import logging
import sys

from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
import farc

from tui_ident import IdentModel, IdentView
from tui_msgs import MsgsModel, MsgsView, StatusModel
from tui_stngs import RadioStngsModel, RadioStngsView

UI_ANIMATE_PERIOD = 0.050  # Taken from asciimatics screen.py


class TxtUiHsm(farc.Ahsm):
    def __init__(self, phy_hsm, lnk_hsm):
        """Language-specific initialization."""
        super().__init__()
        self._ident_model = IdentModel()
        self._msgs_model = MsgsModel(lnk_hsm)
        self._status_model = StatusModel(phy_hsm)
        self._stngs_model = RadioStngsModel(phy_hsm)

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
            Scene([MsgsView(screen, self._msgs_model, self._ident_model, self._stngs_model, self._status_model)], -1, name="Messages"),
            Scene([RadioStngsView(screen, self._stngs_model)], -1, name="Settings"),
        ]

        # If the Identity files are not present, show the Ident page first
        ident_scene = Scene([IdentView(screen, self._ident_model)], -1, name="Identity")
        if self._ident_model.device_cred_exists() and self._ident_model.personal_cert_exists():
            scenes.append(ident_scene)
        else:
            scenes.insert(0, ident_scene)

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
