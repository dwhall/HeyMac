#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

MAC (data link layer) (layer 2) State Machine for a simple text chat app
- collects user input from the terminal
- sends a line of text in a HeyMacCmdTxt packet
- receives text from the RF PHY/MAC layers and displays it on the console
"""


import curses, logging

import pq

import mac_cmds, mac_frame


class ChatAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: ChatAhsm:initial
        """
        # Incoming signals
        pq.Framework.subscribe("TBD", me)

        # Init a timer event
        me.tmr = pq.TimeEvent("TMR_TMOUT")

        # Init curses
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        me.stdscr = stdscr

        # Init output window
        y,x = stdscr.getmaxyx()
        me.outwin = stdscr.subwin(y-1,x, 0,0)
        me.outwin.idlok(True)
        me.outwin.scrollok(True)
        me.outwin.setscrreg(1,y-2)
        me.outwin.border()
        me.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac/main.py ]", curses.A_BOLD)
        me.outwin.refresh()

        # Init input window
        me.inwin = stdscr.subwin(1,x, y-1,0)
        me.inwin.scrollok(False)
        me.inwin.refresh()

        return me.tran(me, ChatAhsm.running)


    @staticmethod
    def running(me, event):
        """State: ChatAhsm:running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, ChatAhsm.exiting)

        return me.super(me, me.top)


    @staticmethod
    def exiting(me, event):
        """State: ChatAhsm:exiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            # Curses de-init
            curses.nocbreak()
            me.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            return me.handled(me, event)

        return me.super(me, me.top)
