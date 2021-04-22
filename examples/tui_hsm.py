"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface state machine
"""

import logging

from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
import farc

from heymac.ui import MsgsModel, RadioStngsModel, StatusModel
from heymac.utl import IdentModel
from tui_ident import IdentView
from tui_msgs import MsgsView
from tui_status import StatusView
from tui_stngs import RadioStngsView

UI_ANIMATE_PERIOD = 0.050  # Taken from asciimatics screen.py


class TxtUiHsm(farc.Ahsm):
    def __init__(self, phy_hsm, lnk_hsm):
        """Language-specific initialization."""
        super().__init__()
        self._ident_model = IdentModel()
        self._msgs_model = MsgsModel(lnk_hsm)
        self._status_model = StatusModel(phy_hsm, lnk_hsm)
        self._stngs_model = RadioStngsModel(phy_hsm)

    @farc.Hsm.state
    def _initial(self, event):
        """PseudoState: _initial

        State machine framework initialization
        """
        farc.Signal.register("_UI_KEYCODE")
        self._tmout_evt = farc.TimeEvent("_UI_TMOUT")
        self._one_sec_evt = farc.TimeEvent("_UI_ONE_SEC")
        farc.Framework.subscribe("GPS_GPRMC", self)
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
            self._one_sec_evt.post_every(self, 1.0)
            self._prev_tick = farc.Framework._event_loop.time()

            if (self._ident_model.device_cred_exists()
                    and self._ident_model.personal_cert_exists()):
                start_scene = None
            else:
                start_scene = Scene([], -1, name="Identity")
            self._new_screen(start_scene)
            return self.handled(event)

        elif sig == farc.Signal._UI_TMOUT:
            try:
                self._screen.draw_next_frame()

            except ResizeScreenError as e:
                self._new_screen(e.scene)

            except StopApplication:
                self._screen.close()
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

        elif sig == farc.Signal._UI_ONE_SEC:
            self._msgs_view.update_time()
            return self.handled(event)

        elif sig == farc.Signal.GPS_GPRMC:
            self._status_view.update_gps(event.value)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._tmout_evt.disarm()
            self._one_sec_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _exiting(self, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("UI._exiting")
            farc.Framework.stop()
            return self.handled(event)

        return self.super(self.top)


    def _new_screen(self, start_scene):
        screen = Screen.open()
        screen.clear()
        self._msgs_view = MsgsView(
            screen,
            self._msgs_model,
            self._ident_model,
            self._stngs_model,
            self._status_model)
        self._ident_view = IdentView(screen, self._ident_model)
        self._stngs_view = RadioStngsView(screen, self._stngs_model)
        self._status_view = StatusView(screen, self._stngs_model)
        scenes = [
            Scene([self._msgs_view], -1, name="Messages"),
            Scene([self._ident_view], -1, name="Identity"),
            Scene([self._stngs_view], -1, name="Settings"),
            Scene([self._status_view], -1, name="Status"),
        ]
        screen.set_scenes(scenes, start_scene=start_scene)
        self._screen = screen
