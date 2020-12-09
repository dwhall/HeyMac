#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Application (layer 7) State Machine for a simple text chat app
- collects a line of text from user input from the terminal
- dispatches the text in a HeyMacCmdTxt message to the MAC layer for TX scheduling
- receives text from the MAC layer and displays it on the console
- shows any received beacons just to let you know who is on the air
"""


import curses
import logging

import farc

import phy_sx127x


class ChatAhsm(farc.Ahsm):
    """Runs a basic chat app over phy_sx127x in a curses window
    """
    _PHY_CHAT_SYNC_WORD = 0x99
    _PHY_STNGS_DFLT = (
        ("FLD_RDO_LORA_MODE", 1),
        ("FLD_RDO_FREQ", 432_550_000),
        ("FLD_RDO_MAX_PWR", 7),
        ("FLD_RDO_PA_BOOST", 1),
        ("FLD_LORA_BW", 8), # phy_sx127x.PhySX127x.STNG_LORA_BW_250K
        ("FLD_LORA_SF", 7), # phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS
        ("FLD_LORA_CR", 2), # phy_sx127x.PhySX127x.STNG_LORA_CR_4TO6
        ("FLD_LORA_CRC_EN", 1),
        ("FLD_LORA_SYNC_WORD", _PHY_CHAT_SYNC_WORD),
    )
    _PHY_STNGS_RX = (("FLD_RDO_FREQ", 432_550_000),)
    _PHY_STNGS_TX = (("FLD_RDO_FREQ", 432_550_000),)


    def __init__(self,):
        """Class initialization
        """
        super().__init__()

        self.phy_ahsm = phy_sx127x.PhySX127xAhsm(True)
        self.phy_ahsm.set_dflt_stngs(ChatAhsm._PHY_STNGS_DFLT)
        self.phy_ahsm.set_dflt_rx_clbk(self._phy_rx_clbk)
        self.phy_ahsm.start(10)


    def _phy_rx_clbk(self, rx_time, rx_bytes, rx_rssi, rx_snr):
        """A method given to the PHY layer as a callback.
        The PHY calls this method with these arguments
        when it receives a frame with no errors.
        This method puts the arguments in a container
        and posts a _LNK_RX_FROM_PHY to this state machine.
        """

        scrnmsg = "<rssi=%d dBm, snr=%.3f dB>: %s" \
            % (rx_rssi, rx_snr, rx_bytes.decode())

        # Echo the message to the outwin
        outy,_ = self.outwin.getmaxyx()
        self.outwin.scroll()
        self.outwin.addstr(outy-2, 1, scrnmsg)
        self.outwin.border()
        self.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
        self.outwin.refresh()


    @farc.Hsm.state
    def _initial(self, event):
        """Pseudostate: _initial
        """
        # Incoming signals
        farc.Framework.subscribe("PHY_RXD_DATA", self)

        # Init a timer event
        self.tm_evt = farc.TimeEvent("_APP_CHAT_TM_EVT_TMOUT")

        # Init curses
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        self.stdscr = stdscr

        # Init output window
        y,x = stdscr.getmaxyx()
        self.outwin = stdscr.subwin(y-1,x, 0,0)
        self.outwin.idlok(True)
        self.outwin.scrollok(True)
        outy,outx = self.outwin.getmaxyx()
        self.outwin.setscrreg(1,outy-2)
        self.outwin.border()
        self.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
        self.outwin.refresh()

        # Init input window
        self.inwin = stdscr.subwin(1,x, y-1,0)
        self.inwin.scrollok(False)
        self.inwin.nodelay(True)
        self.inwin.refresh()
        self.inmsg = bytearray()

        return self.tran(self._running)


    @farc.Hsm.state
    def _running(self, event):
        """State: _running
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            self.tm_evt.post_every(self, 0.075)
            return self.handled(event)

        elif sig == farc.Signal._APP_CHAT_TM_EVT_TMOUT:
            # Get all characters into the bytearray
            c = 0
            while c >= 0:
                c = self.inwin.getch()

                # If the user hits enter, collect the bytes and clear the array
                if c in (10, curses.KEY_ENTER):
                    msg = bytes(self.inmsg)
                    self.inmsg = bytearray()

                    # Send the payload to the PHY layer for transmit
                    self.phy_ahsm.post_tx_action(self.phy_ahsm.TM_NOW, ChatAhsm._PHY_STNGS_TX, msg)

                    # Echo the message to the outwin
                    outy,_ = self.outwin.getmaxyx()
                    self.outwin.scroll()
                    self.outwin.addstr(outy-2, 1, msg)
                    self.outwin.border()
                    self.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
                    self.outwin.refresh()

                    # Cleanup the inwin
                    self.inwin.erase()
                    self.inwin.refresh()

                # FIXME:
                # If the user hits backspace, perform screen backspace
                # and remove the last char collected
                #elif c is 127:
                #    if self.inmsg:
                #        backspace(self.inwin)
                #        self.inmsg.pop()

                # Echo input to the inwin and
                # accumulate characters into the message
                elif 0 < c < 255:
                    self.inwin.echochar(c)
                    self.inmsg.append(c)

            return self.handled(event)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self, ChatAhsm._exiting)

        elif sig == farc.Signal.EXIT:
            self.tm_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _exiting(self, event):
        """State: _exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            # Curses de-init
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            return self.handled(event)

        return self.super(self.top)


# FIXME:
#def backspace(win):
#    curses.nocbreak()
#    y,x = win.getyx(win)
#    win.move(y, x)
#    win.delch();
#    curses.cbreak()
#    win.refresh()
#    curses.echo()
