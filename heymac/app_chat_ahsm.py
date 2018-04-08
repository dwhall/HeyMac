#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Application (layer 7) State Machine for a simple text chat app
- collects a line of text from user input from the terminal
- dispatchtes the text in a HeyMacCmdTxt packet to the MAC layer for TX scheduling
- receives text from the MAC layer and displays it on the console
- shows any received beacons just to let you know who is on the air
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
        pq.Framework.subscribe("PHY_RXD_DATA", me)

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
        outy,outx = me.outwin.getmaxyx()
        me.outwin.setscrreg(1,outy-2)
        me.outwin.border()
        me.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
        me.outwin.refresh()

        # Init input window
        me.inwin = stdscr.subwin(1,x, y-1,0)
        me.inwin.scrollok(False)
        me.inwin.nodelay(True)
        me.inwin.refresh()
        me.inmsg = bytearray()

        return me.tran(me, ChatAhsm.running)


    @staticmethod
    def running(me, event):
        """State: ChatAhsm:running
        """

        sig = event.signal
        if sig == pq.Signal.ENTRY:
            me.tmr.postEvery(me, 0.075)
            return me.handled(me, event)

        elif sig == pq.Signal.TMR_TMOUT:
            # Get all characters into the bytearray
            c = 0
            while c >= 0:
                c = me.inwin.getch()

                # If the user hits enter, collect the bytes and clear the array
                if c in (10, curses.KEY_ENTER):
                    msg = bytes(me.inmsg)
                    me.inmsg = bytearray()

                    # Send the payload to the MAC layer
                    txt = mac_cmds.HeyMacCmdTxt()
                    txt.msg = msg
                    pq.Framework.post(pq.Event(pq.Signal.MAC_TX_REQ, txt), "HeyMacAhsm")

                    # Echo the message to the outwin
                    outy,_ = me.outwin.getmaxyx()
                    me.outwin.scroll()
                    me.outwin.addstr(outy-2, 1, msg)
                    me.outwin.border()
                    me.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
                    me.outwin.refresh()

                    # Cleanup the inwin
                    me.inwin.erase()
                    me.inwin.refresh()

                # FIXME:
                # If the user hits backspace, perform screen backspace
                # and remove the last char collected
                #elif c is 127:
                #    if me.inmsg:
                #        backspace(me.inwin)
                #        me.inmsg.pop()

                # Echo input to the inwin and
                # accumulate characters into the message
                elif 0 < c < 255:
                    me.inwin.echochar(c)
                    me.inmsg.append(c)

            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RXD_DATA:

            # Unpack the rxd data to see if it is a CmdTxt
            rx_time, payld, rssi, snr = event.value
            try:
                f = mac_frame.HeyMacFrame(bytes(payld))
                if isinstance(f.data, mac_cmds.HeyMacCmdTxt):
                    scrnmsg = "<rssi=%d dBm, snr=%.3f dB>: %s" \
                        % (rssi, snr, f.data.msg.decode())
                elif isinstance(f.data, mac_cmds.HeyMacCmdBeacon):
                    scrnmsg = "<bcn from %s: rssi=%d dBm, snr=%.3f dB, asn=%d>" \
                        % (f.data.station_id, rssi, snr, f.data.asn)
                else:
                    scrnmsg = b"<pkt not a known MAC cmd>"
            except Exception as e:
                scrnmsg = "# Exception:" + str(e)

            # Echo the message to the outwin
            outy,_ = me.outwin.getmaxyx()
            me.outwin.scroll()
            me.outwin.addstr(outy-2, 1, scrnmsg)
            me.outwin.border()
            me.outwin.addstr(0,4, "[ github.com/dwhall/HeyMac ]", curses.A_BOLD)
            me.outwin.refresh()

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


# FIXME:
#def backspace(win):
#    curses.nocbreak()
#    y,x = win.getyx(win)
#    win.move(y, x)
#    win.delch(); 
#    curses.cbreak()
#    win.refresh()
#    curses.echo()
