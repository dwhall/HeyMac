import asyncio

from furp import *
from gps import GpsAhsm
from ahsm import HeyMac


if __name__ == "__main__":
    # Start state machines
    gps = GpsAhsm(GpsAhsm.initial)
    gps.start(0)

    m = HeyMac()
    m.start(0)

    # Start UI
    loop = asyncio.get_event_loop()
    app = Furp(loop)
    ualoop = urwid.AsyncioEventLoop(loop=loop)
    umloop = urwid.MainLoop(
        app.get_top_level_widget(),
        event_loop=ualoop,
        palette=[("reversed", "standout", "")],
        pop_ups=True,
        unhandled_input=app._on_unhandled_input)
    umloop.run()
